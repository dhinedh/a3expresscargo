from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from sqlalchemy import or_, func
from typing import List, Optional
from decimal import Decimal
import io
import re
import pandas as pd
from database import get_db
import models
import schemas

router = APIRouter(prefix="/api/v1/items", tags=["Items"])


# ─── Tariff Name Search (Typeahead) ──────────────────────────────────────────

@router.get("/search-tariff", response_model=List[schemas.TariffSearchResult])
def search_tariff_by_name(
    q: str = Query(..., min_length=1, description="Item name or HS code fragment to search"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results to return"),
    db: Session = Depends(get_db)
):
    """
    Search tariff_lines by item name / description / HS code for typeahead suggestions.
    Category headers without duty rates auto-expand to their 8-digit child lines with rates.
    """
    clean_q = q.strip()

    matched_lines = (
        db.query(models.TariffLine, models.Chapter)
        .join(models.Chapter, models.TariffLine.chapter_id == models.Chapter.id)
        .filter(
            models.TariffLine.hs_code.isnot(None),
            or_(
                models.TariffLine.hs_code.ilike(f"%{clean_q}%"),
                models.TariffLine.description.ilike(f"%{clean_q}%"),
            )
        )
        .order_by(models.TariffLine.hs_code)
        .all()
    )

    results = []
    seen_ids = set()

    for line, chapter in matched_lines:
        has_rates = any([
            line.general_duty_rate,
            line.vat_rate,
            line.pal_rate,
            line.cess_rate,
            line.sscl_rate,
            line.excise_rate
        ])

        if not has_rates:
            # Expand category heading to its 8-digit leaf lines that have duty rates
            children = (
                db.query(models.TariffLine)
                .filter(
                    models.TariffLine.hs_code.like(f"{line.hs_code}.%"),
                    or_(
                        models.TariffLine.general_duty_rate.isnot(None),
                        models.TariffLine.vat_rate.isnot(None),
                        models.TariffLine.pal_rate.isnot(None),
                        models.TariffLine.cess_rate.isnot(None)
                    )
                )
                .all()
            )
            for child in children:
                if child.id in seen_ids:
                    continue
                seen_ids.add(child.id)

                clean_parent = line.description.strip(" :") if line.description else ""
                full_desc = f"{clean_parent} - {child.description}" if clean_parent else child.description

                results.append(
                    schemas.TariffSearchResult(
                        tariff_line_id=child.id,
                        hs_code=child.hs_code,
                        description=full_desc,
                        unit=child.unit,
                        chapter_number=chapter.chapter_number,
                        chapter_title=chapter.chapter_title,
                        section_number=chapter.section_number,
                        general_duty_rate=child.general_duty_rate,
                        vat_rate=child.vat_rate,
                        pal_rate=child.pal_rate,
                        cess_rate=child.cess_rate,
                        sscl_rate=child.sscl_rate,
                        excise_rate=child.excise_rate,
                    )
                )
        else:
            if line.id in seen_ids:
                continue
            seen_ids.add(line.id)

            full_desc = line.description
            if line.hs_code and "." in line.hs_code:
                parts = line.hs_code.split(".")
                if len(parts) >= 3:
                    parent_code = f"{parts[0]}.{parts[1]}"
                    parent = db.query(models.TariffLine).filter(models.TariffLine.hs_code == parent_code).first()
                    if parent and parent.description:
                        p_desc = parent.description.strip(" :")
                        if p_desc.lower() not in line.description.lower():
                            full_desc = f"{p_desc} - {line.description}"

            results.append(
                schemas.TariffSearchResult(
                    tariff_line_id=line.id,
                    hs_code=line.hs_code,
                    description=full_desc,
                    unit=line.unit,
                    chapter_number=chapter.chapter_number,
                    chapter_title=chapter.chapter_title,
                    section_number=chapter.section_number,
                    general_duty_rate=line.general_duty_rate,
                    vat_rate=line.vat_rate,
                    pal_rate=line.pal_rate,
                    cess_rate=line.cess_rate,
                    sscl_rate=line.sscl_rate,
                    excise_rate=line.excise_rate,
                )
            )

        if len(results) >= limit:
            break

    return results[:limit]


# ─── Item Entry CRUD ──────────────────────────────────────────────────────────

@router.post("", response_model=schemas.ItemEntryResponse, status_code=201)
def create_item_entry(payload: schemas.ItemEntryCreate, db: Session = Depends(get_db)):
    """Create a new item entry and persist to database."""
    # Compute totals if pricing fields are provided
    price = payload.price_per_kg
    qty = payload.total_quantity_kg
    month_qty = payload.per_month_qty_kg

    total_value = (price * qty) if price and qty else None
    per_month_value = (price * month_qty) if price and month_qty else None

    entry = models.ItemEntry(
        item_name=payload.item_name,
        item_category=payload.item_category,
        unit=payload.unit,
        notes=payload.notes,
        currency=payload.currency,
        tariff_line_id=payload.tariff_line_id,
        hs_code=payload.hs_code,
        tariff_description=payload.tariff_description,
        general_duty_rate=payload.general_duty_rate,
        vat_rate=payload.vat_rate,
        pal_rate=payload.pal_rate,
        cess_rate=payload.cess_rate,
        sscl_rate=payload.sscl_rate,
        excise_rate=payload.excise_rate,
        price_per_kg=price,
        total_quantity_kg=qty,
        per_month_qty_kg=month_qty,
        total_value=total_value,
        per_month_value=per_month_value,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("", response_model=schemas.PaginatedItemEntryResponse)
def list_item_entries(
    query: Optional[str] = Query(None, description="Search by item name, HS code, or category"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Fetch all item entries with optional search and pagination."""
    q = db.query(models.ItemEntry)

    if query:
        clean_q = query.strip()
        q = q.filter(
            or_(
                models.ItemEntry.item_name.ilike(f"%{clean_q}%"),
                models.ItemEntry.hs_code.ilike(f"%{clean_q}%"),
                models.ItemEntry.item_category.ilike(f"%{clean_q}%"),
                models.ItemEntry.tariff_description.ilike(f"%{clean_q}%"),
            )
        )

    total = q.count()
    offset = (page - 1) * page_size
    items = q.order_by(models.ItemEntry.created_at.desc()).offset(offset).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
        "items": items,
    }


# ─── Unified Product Search & Bulk Favorites Management ──────────────────────

@router.get("/search-all", response_model=List[schemas.UnifiedProductSearchResult])
def search_all_products(
    q: str = Query(..., min_length=1, description="Item name or HS code search query"),
    limit: int = Query(25, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Unified tokenized search across:
    1. Saved Favorite Items (Item Master)
    2. Vendor Catalog Products (Ragi, Maida, Atta, etc.)
    3. Customer Requirements Products
    4. Popular Default Commodities
    5. Customs Tariff Database (ranked below prefix matches)
    """
    clean_q = q.strip().lower()
    results = []
    seen_keys = set()

    # 1. Gather all catalog products from Vendor Catalogs & Customer Requirements & Popular Defaults
    catalog_items = set()
    popular_defaults = [
        "Ragi", "Maida", "Atta (Wheat Flour)", "Turmeric Powder", "Black Pepper",
        "White Sugar", "Urad Dal", "Toor Dal", "Chana Dal", "Cardamom",
        "Coriander Seeds", "Mustard Seeds", "Refined Sunflower Oil", "Coconut Oil",
        "Basmati Rice", "Raw Cashew Nuts", "Cloves", "Cinnamon", "Red Chilli"
    ]
    for p in popular_defaults:
        catalog_items.add(p)

    # Add vendor supplied products
    vendors = db.query(models.Vendor).all()
    for v in vendors:
        if v.products_supplied:
            for p in v.products_supplied:
                if p and p.strip():
                    catalog_items.add(p.strip())

    # Add customer requirements products
    reqs = db.query(models.ShipmentCustomerRequirement).all()
    for r in reqs:
        if r.product_name and r.product_name.strip():
            catalog_items.add(r.product_name.strip())

    # Add ItemEntry favorites
    item_entries = db.query(models.ItemEntry).all()
    for ie in item_entries:
        if ie.item_name and ie.item_name.strip():
            catalog_items.add(ie.item_name.strip())

    # Filter catalog items matching query
    matching_catalog = [p for p in catalog_items if clean_q in p.lower()]

    COMMODITY_TARIFF_MAP = {
        "ragi": {"hs_code": "1008.29.10", "category": "Kurakkan (Eleusine coracana spp.) / Ragi Grain", "duty": "20%", "vat": "18%", "pal": "Ex"},
        "maida": {"hs_code": "1101.00.10", "category": "Wheat or meslin flour - Of wheat (Maida)", "duty": "20% or Rs.27/kg", "vat": "Ex", "pal": "5%"},
        "atta": {"hs_code": "1101.00.10", "category": "Wheat or meslin flour - Of wheat (Atta)", "duty": "20% or Rs.27/kg", "vat": "Ex", "pal": "5%"},
        "turmeric": {"hs_code": "0910.30.90", "category": "Ginger, saffron, turmeric (curcuma) - Turmeric", "duty": "20%", "vat": "18%", "pal": "10%"},
        "black pepper": {"hs_code": "0904.11.20", "category": "Pepper of the genus Piper - Matured Berries / Black Pepper", "duty": "20%", "vat": "18%", "pal": "Ex"},
        "pepper": {"hs_code": "0904.11.20", "category": "Pepper of the genus Piper - Black Pepper", "duty": "20%", "vat": "18%", "pal": "Ex"},
        "white sugar": {"hs_code": "1701.99.10", "category": "Cane or beet sugar - Refined White Sugar", "duty": "Rs.30/kg", "vat": "18%", "pal": "Ex"},
        "sugar": {"hs_code": "1701.99.10", "category": "Cane or beet sugar - Refined White Sugar", "duty": "Rs.30/kg", "vat": "18%", "pal": "Ex"},
        "basmati rice": {"hs_code": "1006.20.00", "category": "Rice - Husked (brown) / Basmati Rice", "duty": "20% or Rs.80/kg", "vat": "18%", "pal": "Ex"},
        "rice": {"hs_code": "1006.20.00", "category": "Rice - Husked (brown)", "duty": "20% or Rs.80/kg", "vat": "18%", "pal": "Ex"},
        "cashew": {"hs_code": "2008.19.10", "category": "Cashew nuts, prepared or preserved", "duty": "20% or Rs.160/kg", "vat": "18%", "pal": "10%"},
        "cardamom": {"hs_code": "3301.90.95", "category": "Nutmeg, mace and cardamoms - Cardamom", "duty": "10%", "vat": "18%", "pal": "Ex"},
        "cinnamon": {"hs_code": "0906.20.10", "category": "Cinnamon (Cinnamomum zeylanicum Blume) crushed / ground", "duty": "20%", "vat": "18%", "pal": "Ex"},
        "cloves": {"hs_code": "0907.10.12", "category": "Cloves (whole fruit, cloves and stems)", "duty": "20%", "vat": "18%", "pal": "Ex"},
        "red chilli": {"hs_code": "0904.21.10", "category": "Fruits of the genus Capsicum - Chillies", "duty": "Rs.100/kg", "vat": "18%", "pal": "Ex"},
        "chilli": {"hs_code": "0904.21.10", "category": "Fruits of the genus Capsicum - Chillies", "duty": "Rs.100/kg", "vat": "18%", "pal": "Ex"},
        "mustard": {"hs_code": "1207.50.00", "category": "Mustard seeds", "duty": "20%", "vat": "18%", "pal": "Ex"},
        "sunflower oil": {"hs_code": "1206.00.00", "category": "Sunflower-seed oil and fractions thereof", "duty": "10%", "vat": "18%", "pal": "Ex"},
        "coconut oil": {"hs_code": "0801.19.20", "category": "Coconut (copra) oil and fractions thereof", "duty": "20%", "vat": "18%", "pal": "Ex"},
        "urad dal": {"hs_code": "0713.31.19", "category": "Dried leguminous vegetables - Urad Dal / Beans", "duty": "Rs.70/kg", "vat": "18%", "pal": "Ex"},
        "toor dal": {"hs_code": "0713.20.20", "category": "Dried leguminous vegetables - Toor Dal / Chickpeas", "duty": "20%", "vat": "18%", "pal": "Ex"},
        "chana dal": {"hs_code": "0713.20.10", "category": "Dried leguminous vegetables - Chana Dal / Chickpeas", "duty": "20%", "vat": "18%", "pal": "Ex"},
    }

    for item in matching_catalog:
        key = f"FAV_{item.strip().lower()}"
        if key in seen_keys:
            continue
        seen_keys.add(key)
        
        # Check if there's an ItemEntry in DB with full specs
        db_entry = next((ie for ie in item_entries if ie.item_name.strip().lower() == item.lower()), None)

        # Match against COMMODITY_TARIFF_MAP if db_entry does not specify hs_code
        mapped_info = None
        for key_term, info in COMMODITY_TARIFF_MAP.items():
            if key_term in item.lower():
                mapped_info = info
                break

        final_hsn = db_entry.hs_code if (db_entry and db_entry.hs_code) else (mapped_info["hs_code"] if mapped_info else None)
        final_category = db_entry.item_category if (db_entry and db_entry.item_category) else (mapped_info["category"] if mapped_info else f"{item} Commodity")
        final_desc = db_entry.tariff_description if (db_entry and db_entry.tariff_description) else (mapped_info["category"] if mapped_info else item)
        final_duty = db_entry.general_duty_rate if (db_entry and db_entry.general_duty_rate) else (mapped_info["duty"] if mapped_info else "15%")
        final_vat = db_entry.vat_rate if (db_entry and db_entry.vat_rate) else (mapped_info["vat"] if mapped_info else "18%")
        final_pal = db_entry.pal_rate if (db_entry and db_entry.pal_rate) else (mapped_info["pal"] if mapped_info else "Ex")

        results.append(
            schemas.UnifiedProductSearchResult(
                source="FAVORITE",
                id=db_entry.id if db_entry else 0,
                tariff_line_id=db_entry.tariff_line_id if db_entry else None,
                item_name=item,
                hs_code=final_hsn,
                description=final_desc,
                product_category=final_category,
                unit=db_entry.unit if db_entry else "KG",
                currency=db_entry.currency if db_entry else "INR",
                purchase_price=(db_entry.purchase_price or db_entry.price_per_kg) if db_entry else None,
                weight_val=db_entry.weight_val if db_entry else 1.0,
                weight_unit=db_entry.weight_unit if db_entry else "KG",
                general_duty_rate=final_duty,
                vat_rate=final_vat,
                pal_rate=final_pal,
                cess_rate=db_entry.cess_rate if db_entry else None,
                sscl_rate=db_entry.sscl_rate if db_entry else None,
                excise_rate=db_entry.excise_rate if db_entry else None,
                scl_rate=db_entry.scl_rate if db_entry else None,
            )
        )

    # 2. Search Tariff Lines
    raw_words = re.findall(r'\b[a-zA-Z]{3,}\b', clean_q)
    stop_words = {'pack', 'box', 'pcs', 'nos', 'qty', 'unit', 'units', 'kilo', 'gram', 'grams', 'item', 'items', 'the', 'and', 'for', 'with'}
    tokens = set()
    for w in raw_words:
        wl = w.lower()
        if wl in stop_words:
            continue
        tokens.add(wl)

    tariff_filters = [
        models.TariffLine.hs_code.ilike(f"%{clean_q}%"),
        models.TariffLine.description.ilike(f"%{clean_q}%")
    ]
    for t in tokens:
        tariff_filters.append(models.TariffLine.description.ilike(f"%{t}%"))

    tariff_lines = (
        db.query(models.TariffLine)
        .filter(
            models.TariffLine.hs_code.isnot(None),
            models.TariffLine.description.isnot(None),
            models.TariffLine.description != "",
            ~models.TariffLine.hs_code.ilike("Chapter%"),
            or_(*tariff_filters)
        )
        .order_by(models.TariffLine.hs_code)
        .all()
    )

    seen_line_ids = set()

    for line in tariff_lines:
        has_rates = any([
            line.general_duty_rate,
            line.vat_rate,
            line.pal_rate,
            line.cess_rate,
            line.sscl_rate,
            line.excise_rate,
            line.scl_rate
        ])

        if not has_rates:
            children = (
                db.query(models.TariffLine)
                .filter(
                    models.TariffLine.hs_code.like(f"{line.hs_code}.%"),
                    or_(
                        models.TariffLine.general_duty_rate.isnot(None),
                        models.TariffLine.vat_rate.isnot(None),
                        models.TariffLine.pal_rate.isnot(None),
                        models.TariffLine.cess_rate.isnot(None)
                    )
                )
                .all()
            )
            for child in children:
                if child.id in seen_line_ids:
                    continue
                seen_line_ids.add(child.id)

                clean_parent = line.description.strip(" :") if line.description else ""
                full_desc = f"{clean_parent} - {child.description}" if clean_parent and clean_parent.lower() not in child.description.lower() else child.description
                key = f"TARIFF_{child.id}"
                if key in seen_keys:
                    continue
                seen_keys.add(key)

                results.append(
                    schemas.UnifiedProductSearchResult(
                        source="TARIFF",
                        id=child.id,
                        tariff_line_id=child.id,
                        item_name=full_desc,
                        hs_code=child.hs_code,
                        description=full_desc,
                        product_category=None,
                        unit=child.unit or "PCS",
                        currency="INR",
                        purchase_price=None,
                        weight_val=None,
                        weight_unit="KG",
                        general_duty_rate=child.general_duty_rate,
                        vat_rate=child.vat_rate,
                        pal_rate=child.pal_rate,
                        cess_rate=child.cess_rate,
                        sscl_rate=child.sscl_rate,
                        excise_rate=child.excise_rate,
                        scl_rate=child.scl_rate,
                    )
                )
        else:
            if line.id in seen_line_ids:
                continue
            seen_line_ids.add(line.id)

            full_desc = line.description.strip()
            if line.hs_code and "." in line.hs_code:
                parts = line.hs_code.split(".")
                if len(parts) >= 3:
                    parent_code = f"{parts[0]}.{parts[1]}"
                    parent = db.query(models.TariffLine).filter(models.TariffLine.hs_code == parent_code).first()
                    if parent and parent.description:
                        p_desc = parent.description.strip(" :")
                        if p_desc.lower() not in line.description.lower():
                            full_desc = f"{p_desc} - {line.description}"

            key = f"TARIFF_{line.id}"
            if key in seen_keys:
                continue
            seen_keys.add(key)

            results.append(
                schemas.UnifiedProductSearchResult(
                    source="TARIFF",
                    id=line.id,
                    tariff_line_id=line.id,
                    item_name=full_desc,
                    hs_code=line.hs_code,
                    description=full_desc,
                    product_category=None,
                    unit=line.unit or "PCS",
                    currency="INR",
                    purchase_price=None,
                    weight_val=None,
                    weight_unit="KG",
                    general_duty_rate=line.general_duty_rate,
                    vat_rate=line.vat_rate,
                    pal_rate=line.pal_rate,
                    cess_rate=line.cess_rate,
                    sscl_rate=line.sscl_rate,
                    excise_rate=line.excise_rate,
                    scl_rate=line.scl_rate,
                )
            )

    # 3. RELEVANCE RANKING SORT: Put exact & prefix matches (e.g. Ragi for 'rag') at the VERY TOP!
    def calc_relevance(item: schemas.UnifiedProductSearchResult) -> int:
        name = (item.item_name or "").lower()
        if name == clean_q:
            return 1000
        if name.startswith(clean_q):
            return 800
        # Check word boundaries
        words = name.split()
        if any(w.startswith(clean_q) for w in words):
            return 600
        if item.source == "FAVORITE":
            return 400
        return 100

    results.sort(key=calc_relevance, reverse=True)

    return results[:limit]



@router.post("/upsert-favorite", response_model=schemas.ItemEntryResponse)
def upsert_favorite_item(payload: schemas.ItemEntryCreate, db: Session = Depends(get_db)):
    """Save or update an item in Item Master / Favorites by product name."""
    clean_name = payload.item_name.strip()
    entry = db.query(models.ItemEntry).filter(func.lower(models.ItemEntry.item_name) == clean_name.lower()).first()

    if not entry:
        entry = models.ItemEntry(item_name=clean_name)
        db.add(entry)

    entry.item_category = payload.item_category
    entry.unit = payload.unit or "PCS"
    entry.currency = payload.currency or "INR"
    entry.hs_code = payload.hs_code
    entry.tariff_line_id = payload.tariff_line_id
    entry.tariff_description = payload.tariff_description
    entry.general_duty_rate = payload.general_duty_rate
    entry.vat_rate = payload.vat_rate
    entry.pal_rate = payload.pal_rate
    entry.cess_rate = payload.cess_rate
    entry.sscl_rate = payload.sscl_rate
    entry.excise_rate = payload.excise_rate
    entry.scl_rate = payload.scl_rate
    entry.weight_val = payload.weight_val or Decimal("0")
    entry.weight_unit = payload.weight_unit or "KG"
    entry.purchase_price = payload.purchase_price
    entry.is_favorite = True

    db.commit()
    db.refresh(entry)
    return entry


@router.post("/bulk-upload-excel")
async def bulk_upload_favorite_products(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Bulk upload favorite products from an Excel file (.xlsx / .xls)."""
    if not (file.filename.endswith(".xlsx") or file.filename.endswith(".xls")):
        raise HTTPException(status_code=400, detail="Only .xlsx or .xls files allowed")

    contents = await file.read()
    try:
        df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read Excel file: {str(e)}")

    df.columns = [str(c).strip().lower().replace(" ", "_").replace("-", "_") for c in df.columns]

    inserted_count = 0
    updated_count = 0
    errors = []

    for index, row in df.iterrows():
        try:
            name_val = row.get("product_name") or row.get("item_name") or row.get("name") or row.get("description")
            if not name_val or pd.isna(name_val):
                continue
            clean_name = str(name_val).strip()

            hsn_val = str(row.get("hsn_code") or row.get("hs_code") or "").strip()
            cat_val = str(row.get("product_category") or row.get("category") or "").strip()
            unit_val = str(row.get("unit") or "PCS").strip()
            curr_val = str(row.get("currency") or "INR").strip()

            price_raw = row.get("purchase_price") or row.get("price") or row.get("price_per_unit")
            price_val = Decimal(str(price_raw)) if (price_raw is not None and not pd.isna(price_raw)) else Decimal("0")

            wt_raw = row.get("unit_weight") or row.get("weight") or row.get("weight_val")
            wt_val = Decimal(str(wt_raw)) if (wt_raw is not None and not pd.isna(wt_raw)) else Decimal("0")

            wt_unit_val = str(row.get("weight_unit") or "KG").strip()

            duty_val = str(row.get("general_duty") or row.get("duty_rate") or row.get("duty") or "").strip()
            vat_val = str(row.get("vat_rate") or row.get("vat") or "").strip()
            pal_val = str(row.get("pal_rate") or row.get("pal") or "").strip()
            cess_val = str(row.get("cess_rate") or row.get("cess") or "").strip()
            sscl_val = str(row.get("sscl_rate") or row.get("sscl") or "").strip()

            entry = db.query(models.ItemEntry).filter(func.lower(models.ItemEntry.item_name) == clean_name.lower()).first()

            if entry:
                updated_count += 1
            else:
                entry = models.ItemEntry(item_name=clean_name)
                db.add(entry)
                inserted_count += 1

            entry.hs_code = hsn_val or entry.hs_code
            entry.item_category = cat_val or entry.item_category
            entry.unit = unit_val or entry.unit
            entry.currency = curr_val or entry.currency
            entry.purchase_price = price_val if price_val > 0 else entry.purchase_price
            entry.weight_val = wt_val if wt_val > 0 else entry.weight_val
            entry.weight_unit = wt_unit_val or entry.weight_unit
            entry.general_duty_rate = duty_val or entry.general_duty_rate
            entry.vat_rate = vat_val or entry.vat_rate
            entry.pal_rate = pal_val or entry.pal_rate
            entry.cess_rate = cess_val or entry.cess_rate
            entry.sscl_rate = sscl_val or entry.sscl_rate
            entry.is_favorite = True

        except Exception as err:
            errors.append(f"Row {index + 2}: {str(err)}")

    db.commit()

    return {
        "status": "success",
        "inserted": inserted_count,
        "updated": updated_count,
        "total_processed": inserted_count + updated_count,
        "errors": errors
    }


@router.get("/{item_id}", response_model=schemas.ItemEntryResponse)
def get_item_entry(item_id: int, db: Session = Depends(get_db)):
    """Get a single item entry by ID."""
    entry = db.query(models.ItemEntry).filter(models.ItemEntry.id == item_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Item entry not found")
    return entry


@router.put("/{item_id}", response_model=schemas.ItemEntryResponse)
def update_item_entry(item_id: int, payload: schemas.ItemEntryUpdate, db: Session = Depends(get_db)):
    """Update an existing item entry."""
    entry = db.query(models.ItemEntry).filter(models.ItemEntry.id == item_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Item entry not found")

    update_data = payload.dict(exclude_unset=True)
    for field, val in update_data.items():
        setattr(entry, field, val)

    # Re-compute totals if price or qty fields were updated
    price = entry.price_per_kg
    qty = entry.total_quantity_kg
    month_qty = entry.per_month_qty_kg

    if price is not None and qty is not None:
        entry.total_value = Decimal(str(price)) * Decimal(str(qty))
    if price is not None and month_qty is not None:
        entry.per_month_value = Decimal(str(price)) * Decimal(str(month_qty))

    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{item_id}", status_code=204)
def delete_item_entry(item_id: int, db: Session = Depends(get_db)):
    """Delete an item entry by ID."""
    entry = db.query(models.ItemEntry).filter(models.ItemEntry.id == item_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Item entry not found")
    db.delete(entry)
    db.commit()
    return None



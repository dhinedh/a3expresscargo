import json
import logging
from typing import Dict, Any, List
from database import get_mongo_db, SessionLocal
import models

logger = logging.getLogger("mongo_sync")

def sync_shipment_to_mongo(shipment_id: int):
    """Save/update a full JSON snapshot of a shipment into MongoDB Atlas."""
    db = get_mongo_db()
    if db is None:
        return

    sql_db = SessionLocal()
    try:
        sh = sql_db.query(models.Shipment).filter(models.Shipment.id == shipment_id).first()
        if not sh:
            return

        # Build full JSON document representation
        cust_list = [{"id": c.id, "name": c.name, "code": c.code, "country": c.country} for c in sh.customers]
        prod_list = []
        for p in sh.products:
            prod_list.append({
                "id": p.id,
                "customer_id": p.customer_id,
                "product_name": p.product_name,
                "hs_code": p.hs_code,
                "quantity": float(p.quantity or 0.0),
                "unit": p.unit,
                "purchase_price": float(p.purchase_price or 0.0),
                "purchase_currency": p.purchase_currency,
                "freight_cost_inr": float(p.freight_cost_inr or 0.0),
                "calculated_duty_lkr": float(p.calculated_duty_lkr or 0.0),
                "total_cost_lkr": float(p.total_cost_lkr or 0.0),
                "final_quotation_price": float(p.final_quotation_price or 0.0),
            })

        req_list = []
        reqs = sql_db.query(models.ShipmentCustomerRequirement).filter(models.ShipmentCustomerRequirement.shipment_id == shipment_id).all()
        for r in reqs:
            req_list.append({
                "id": r.id,
                "customer_id": r.customer_id,
                "customer_name": r.customer_name,
                "product_name": r.product_name,
                "hs_code": r.hs_code,
                "required_quantity": float(r.required_quantity or 0.0),
                "unit": r.unit,
                "notes": r.notes
            })

        alloc_list = []
        allocs = sql_db.query(models.ShipmentVendorAllocation).filter(models.ShipmentVendorAllocation.shipment_id == shipment_id).all()
        for a in allocs:
            alloc_list.append({
                "id": a.id,
                "requirement_id": a.requirement_id,
                "vendor_id": a.vendor_id,
                "allocated_quantity": float(a.allocated_quantity or 0.0),
                "allocated_unit": a.allocated_unit,
                "vendor_quote_price": float(a.vendor_quote_price or 0.0),
                "vendor_quote_currency": a.vendor_quote_currency,
                "rfq_sent": a.rfq_sent,
                "status": a.status
            })

        doc = {
            "_id": sh.id,
            "id": sh.id,
            "financial_year": sh.financial_year,
            "sequence_number": sh.sequence_number,
            "shipment_no": sh.shipment_no,
            "shipment_date": sh.shipment_date,
            "status": sh.status,
            "current_stage": sh.current_stage,
            "usd_rate": float(sh.usd_rate or 305.0),
            "lkr_inr_rate": float(sh.lkr_inr_rate or 3.65),
            "profit_margin_pct": float(sh.profit_margin_pct or 15.0),
            "customers": cust_list,
            "products": prod_list,
            "requirements": req_list,
            "allocations": alloc_list,
            "updated_at": sh.updated_at.isoformat() if sh.updated_at else None
        }

        db.shipments_cloud.replace_one({"_id": sh.id}, doc, upsert=True)
        logger.info(f"Synced Shipment #{sh.shipment_no} to MongoDB Atlas.")

    except Exception as e:
        logger.error(f"Error syncing shipment to Mongo Atlas: {e}")
    finally:
        sql_db.close()


def restore_shipments_from_mongo(db_session=None):
    """Auto-restore shipments from MongoDB Atlas if local database container restarted."""
    db = get_mongo_db()
    if db is None:
        return

    sql_db = db_session if db_session is not None else SessionLocal()
    should_close = db_session is None
    try:
        cloud_shipments = list(db.shipments_cloud.find())
        if not cloud_shipments:
            return

        for doc in cloud_shipments:
            s_id = doc.get("id")
            existing = sql_db.query(models.Shipment).filter(models.Shipment.id == s_id).first()
            if not existing:
                sh = models.Shipment(
                    id=s_id,
                    financial_year=doc.get("financial_year", "2026-27"),
                    sequence_number=doc.get("sequence_number", 1),
                    shipment_no=doc.get("shipment_no", f"AEC/{s_id}/2026-27"),
                    shipment_date=doc.get("shipment_date"),
                    status=doc.get("status", "DRAFT"),
                    current_stage=doc.get("current_stage", "1_SHIPMENT_CREATION"),
                    usd_rate=doc.get("usd_rate", 305.0),
                    lkr_inr_rate=doc.get("lkr_inr_rate", 3.65),
                    profit_margin_pct=doc.get("profit_margin_pct", 15.0)
                )
                sql_db.add(sh)
                sql_db.flush()

                # Restore Customers
                for c in doc.get("customers", []):
                    c_obj = sql_db.query(models.Customer).filter(models.Customer.name == c["name"]).first()
                    if not c_obj:
                        c_obj = models.Customer(name=c["name"], code=c.get("code", c["name"][:4].upper()), country=c.get("country", "Sri Lanka"))
                        sql_db.add(c_obj)
                        sql_db.flush()
                    sc = models.ShipmentCustomer(shipment_id=sh.id, customer_id=c_obj.id)
                    sql_db.add(sc)

                # Restore Requirements
                for r in doc.get("requirements", []):
                    req = models.ShipmentCustomerRequirement(
                        shipment_id=sh.id,
                        customer_id=r.get("customer_id", 1),
                        customer_name=r.get("customer_name", "Customer 1"),
                        product_name=r.get("product_name"),
                        hs_code=r.get("hs_code"),
                        required_quantity=r.get("required_quantity", 1.0),
                        unit=r.get("unit", "CARTON"),
                        notes=r.get("notes")
                    )
                    sql_db.add(req)

                # Restore Products
                for p in doc.get("products", []):
                    sp = models.ShipmentProduct(
                        shipment_id=sh.id,
                        customer_id=p.get("customer_id", 1),
                        product_name=p.get("product_name"),
                        hs_code=p.get("hs_code"),
                        quantity=p.get("quantity", 1.0),
                        unit=p.get("unit", "CARTON"),
                        purchase_price=p.get("purchase_price", 0.0),
                        purchase_currency=p.get("purchase_currency", "INR"),
                        freight_cost_inr=p.get("freight_cost_inr", 0.0),
                        calculated_duty_lkr=p.get("calculated_duty_lkr", 0.0),
                        total_cost_lkr=p.get("total_cost_lkr", 0.0),
                        final_quotation_price=p.get("final_quotation_price", 0.0)
                    )
                    sql_db.add(sp)

                # Restore Allocations
                for a in doc.get("allocations", []):
                    alloc = models.ShipmentVendorAllocation(
                        shipment_id=sh.id,
                        requirement_id=a.get("requirement_id"),
                        vendor_id=a.get("vendor_id"),
                        allocated_quantity=a.get("allocated_quantity", 1.0),
                        allocated_unit=a.get("allocated_unit", "CARTON"),
                        vendor_quote_price=a.get("vendor_quote_price", 0.0),
                        vendor_quote_currency=a.get("vendor_quote_currency", "INR"),
                        rfq_sent=a.get("rfq_sent", False),
                        status=a.get("status", "ALLOCATED")
                    )
                    sql_db.add(alloc)

                # Restore Actuals
                act = sql_db.query(models.ShipmentActual).filter(models.ShipmentActual.shipment_id == sh.id).first()
                if not act:
                    act = models.ShipmentActual(shipment_id=sh.id)
                    sql_db.add(act)

                sql_db.commit()
                logger.info(f"Restored Shipment #{sh.shipment_no} from MongoDB Atlas.")

    except Exception as e:
        sql_db.rollback()
        logger.error(f"Error restoring shipments from Mongo: {e}")
    finally:
        if should_close:
            sql_db.close()

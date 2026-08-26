import React, { useState, useRef, useEffect } from 'react';
import {
  Ship,
  Users,
  Truck,
  BarChart3,
  ChevronDown,
  Plus,
  Package,
  History,
  FileText,
  User,
  Shield,
  Layers,
  Database,
  PackagePlus,
  Sparkles
} from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onOpenCreateShipment: () => void;
  onOpenAddVendor: () => void;
  onOpenAddCustomer: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  onOpenCreateShipment,
  onOpenAddVendor,
  onOpenAddCustomer
}) => {
  const [openMenu, setOpenMenu] = useState<string | null>(null);
  const navRef = useRef<HTMLDivElement>(null);

  // Close dropdowns on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (navRef.current && !navRef.current.contains(e.target as Node)) {
        setOpenMenu(null);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleMenu = (menuName: string) => {
    setOpenMenu(prev => (prev === menuName ? null : menuName));
  };

  const handleMenuClick = (action: () => void) => {
    action();
    setOpenMenu(null);
  };

  return (
    <header className="bg-slate-900 text-white shadow-md border-b border-slate-800 sticky top-0 z-40 font-sans">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Logo & Brand */}
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => setActiveTab('shipments')}>
          <div className="bg-blue-600 p-2.5 rounded-2xl text-white shadow-md shadow-blue-900/30 flex items-center justify-center">
            <Ship className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-lg font-extrabold tracking-tight flex items-center gap-2 text-white">
              A3 EXPRESS SOFTWARE
              <span className="text-[10px] font-mono font-bold bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded-full border border-blue-400/30">
                v2.0 PRO
              </span>
            </h1>
            <p className="text-xs text-slate-400">Shipment Management, Tariff Calculation & Freight Documentation System</p>
          </div>
        </div>

        {/* Dropdown Navigation Bar */}
        <nav ref={navRef} className="flex flex-wrap items-center gap-1.5 bg-slate-800/90 p-1.5 rounded-2xl border border-slate-700/60 shadow-lg">
          
          {/* 1. SHIPMENT MENU */}
          <div className="relative">
            <button
              onClick={() => toggleMenu('shipment')}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                activeTab === 'shipments' || activeTab === 'shipment_detail' || openMenu === 'shipment'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/60'
              }`}
            >
              <Ship className="w-4 h-4 text-blue-400" />
              <span>Shipment</span>
              <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${openMenu === 'shipment' ? 'rotate-180' : ''}`} />
            </button>

            {openMenu === 'shipment' && (
              <div className="absolute left-0 mt-2 w-56 bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl p-1.5 z-50 animate-fadeIn">
                <button
                  onClick={() => handleMenuClick(onOpenCreateShipment)}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-bold text-blue-400 hover:bg-blue-600/20 rounded-xl transition-all cursor-pointer text-left"
                >
                  <Plus className="w-4 h-4 text-blue-400" />
                  <span>Create New Shipment</span>
                </button>
                <button
                  onClick={() => handleMenuClick(() => setActiveTab('shipments'))}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-800 rounded-xl transition-all cursor-pointer text-left"
                >
                  <Package className="w-4 h-4 text-emerald-400" />
                  <span>Current Shipments</span>
                </button>
                <button
                  onClick={() => handleMenuClick(() => setActiveTab('shipments'))}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-800 rounded-xl transition-all cursor-pointer text-left"
                >
                  <History className="w-4 h-4 text-purple-400" />
                  <span>Shipment History</span>
                </button>
              </div>
            )}
          </div>

          {/* 2. VENDOR MENU */}
          <div className="relative">
            <button
              onClick={() => toggleMenu('vendor')}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                activeTab === 'vendors' || openMenu === 'vendor'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/60'
              }`}
            >
              <Truck className="w-4 h-4 text-amber-400" />
              <span>Vendor</span>
              <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${openMenu === 'vendor' ? 'rotate-180' : ''}`} />
            </button>

            {openMenu === 'vendor' && (
              <div className="absolute left-0 mt-2 w-52 bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl p-1.5 z-50 animate-fadeIn">
                <button
                  onClick={() => handleMenuClick(() => setActiveTab('vendors'))}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-800 rounded-xl transition-all cursor-pointer text-left"
                >
                  <Truck className="w-4 h-4 text-amber-400" />
                  <span>Vendor List</span>
                </button>
                <button
                  onClick={() => handleMenuClick(onOpenAddVendor)}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-bold text-amber-400 hover:bg-amber-500/20 rounded-xl transition-all cursor-pointer text-left"
                >
                  <Plus className="w-4 h-4 text-amber-400" />
                  <span>Add Vendor</span>
                </button>
              </div>
            )}
          </div>

          {/* 3. CUSTOMER MENU */}
          <div className="relative">
            <button
              onClick={() => toggleMenu('customer')}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                activeTab === 'customers' || openMenu === 'customer'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/60'
              }`}
            >
              <Users className="w-4 h-4 text-emerald-400" />
              <span>Customer</span>
              <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${openMenu === 'customer' ? 'rotate-180' : ''}`} />
            </button>

            {openMenu === 'customer' && (
              <div className="absolute left-0 mt-2 w-52 bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl p-1.5 z-50 animate-fadeIn">
                <button
                  onClick={() => handleMenuClick(() => setActiveTab('customers'))}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-800 rounded-xl transition-all cursor-pointer text-left"
                >
                  <Users className="w-4 h-4 text-emerald-400" />
                  <span>Customer List</span>
                </button>
                <button
                  onClick={() => handleMenuClick(onOpenAddCustomer)}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-bold text-emerald-400 hover:bg-emerald-500/20 rounded-xl transition-all cursor-pointer text-left"
                >
                  <Plus className="w-4 h-4 text-emerald-400" />
                  <span>Add Customer</span>
                </button>
              </div>
            )}
          </div>

          {/* 4. REPORTS MENU */}
          <div className="relative">
            <button
              onClick={() => toggleMenu('reports')}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                activeTab === 'dashboard' || activeTab === 'items' || activeTab === 'tariff' || openMenu === 'reports'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/60'
              }`}
            >
              <BarChart3 className="w-4 h-4 text-purple-400" />
              <span>Reports</span>
              <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${openMenu === 'reports' ? 'rotate-180' : ''}`} />
            </button>

            {openMenu === 'reports' && (
              <div className="absolute left-0 mt-2 w-60 bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl p-1.5 z-50 animate-fadeIn">
                <button
                  onClick={() => handleMenuClick(() => setActiveTab('dashboard'))}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-800 rounded-xl transition-all cursor-pointer text-left"
                >
                  <BarChart3 className="w-4 h-4 text-purple-400" />
                  <span>Financial Reports</span>
                </button>
                <button
                  onClick={() => handleMenuClick(() => setActiveTab('shipments'))}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-800 rounded-xl transition-all cursor-pointer text-left"
                >
                  <Ship className="w-4 h-4 text-blue-400" />
                  <span>Shipment Tracker</span>
                </button>
                <button
                  onClick={() => handleMenuClick(() => setActiveTab('items'))}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-800 rounded-xl transition-all cursor-pointer text-left"
                >
                  <PackagePlus className="w-4 h-4 text-amber-400" />
                  <span>Current Shipment Report</span>
                </button>
                <button
                  onClick={() => handleMenuClick(() => setActiveTab('tariff'))}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-800 rounded-xl transition-all cursor-pointer text-left border-t border-slate-800 mt-1 pt-2"
                >
                  <Database className="w-4 h-4 text-cyan-400" />
                  <span>Tariff DB Master</span>
                </button>
              </div>
            )}
          </div>

          {/* 5. PROFILE / ACCOUNT MENU */}
          <div className="relative">
            <button
              onClick={() => toggleMenu('profile')}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                openMenu === 'profile'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/60'
              }`}
            >
              <User className="w-4 h-4 text-cyan-400" />
              <span>Profile / Account</span>
              <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${openMenu === 'profile' ? 'rotate-180' : ''}`} />
            </button>

            {openMenu === 'profile' && (
              <div className="absolute right-0 mt-2 w-64 bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl p-3 z-50 animate-fadeIn space-y-3">
                <div className="flex items-center gap-3 pb-3 border-b border-slate-800">
                  <div className="w-9 h-9 rounded-xl bg-blue-600 text-white font-extrabold flex items-center justify-center text-sm shadow-sm">
                    A3
                  </div>
                  <div>
                    <div className="text-xs font-bold text-white">A3 Express Cargo Admin</div>
                    <div className="text-[10px] text-slate-400">admin@a3expresscargo.com</div>
                  </div>
                </div>

                <div className="space-y-1 text-xs font-medium">
                  <div className="flex justify-between py-1 text-slate-300">
                    <span>Role:</span>
                    <span className="font-bold text-blue-400">System Operations Admin</span>
                  </div>
                  <div className="flex justify-between py-1 text-slate-300">
                    <span>Active Region:</span>
                    <span className="font-bold text-emerald-400">India &bull; Sri Lanka</span>
                  </div>
                  <div className="flex justify-between py-1 text-slate-300">
                    <span>Environment:</span>
                    <span className="font-bold text-amber-400">v2.0 PRO Live Cloud</span>
                  </div>
                </div>
              </div>
            )}
          </div>

        </nav>
      </div>
    </header>
  );
};

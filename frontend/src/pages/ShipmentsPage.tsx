import React, { useState, useEffect } from 'react';
import { Ship, Plus, Calendar, ChevronRight, CheckCircle2, Clock, XCircle, AlertCircle, Zap, ArrowRight, Layers } from 'lucide-react';
import type { Shipment } from '../types';
import { apiClient } from '../api/client';
import { ShipmentWizardModal } from '../components/ShipmentWizardModal';

interface ShipmentsPageProps {
  onSelectShipment: (shipmentId: number) => void;
}

export const ShipmentsPage: React.FC<ShipmentsPageProps> = ({ onSelectShipment }) => {
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [loading, setLoading] = useState(false);
  const [showWizardModal, setShowWizardModal] = useState(false);
  const [wizardResumeState, setWizardResumeState] = useState<{ shipmentId?: number; step?: number } | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const sData = await apiClient.getShipments();
      setShipments(sData);
    } catch (err) {
      console.error('Failed to load shipments:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Most recent in-progress / draft shipment for 1-click resumption
  const inProgressShipment = shipments.find(s => s.status !== 'COMPLETED' && s.status !== 'CANCELLED') || shipments[0];

  const handleResumeShipment = (s: Shipment) => {
    const lastWizShipmentId = localStorage.getItem('a3_last_wizard_shipment_id');
    const lastWizStep = localStorage.getItem('a3_last_wizard_step');

    if (lastWizShipmentId === String(s.id) && lastWizStep) {
      setWizardResumeState({
        shipmentId: s.id,
        step: Number(lastWizStep)
      });
      setShowWizardModal(true);
    } else if (s.status === 'DRAFT' && (!s.products || s.products.length === 0)) {
      setWizardResumeState({
        shipmentId: s.id,
        step: 2
      });
      setShowWizardModal(true);
    } else {
      onSelectShipment(s.id);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200"><CheckCircle2 className="w-3 h-3" /> Completed</span>;
      case 'SHIPPED':
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200"><Ship className="w-3 h-3" /> Shipped</span>;
      case 'CONFIGURED':
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200"><Clock className="w-3 h-3" /> Configured</span>;
      case 'CANCELLED':
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-50 text-red-700 border border-red-200"><XCircle className="w-3 h-3" /> Cancelled</span>;
      default:
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200"><AlertCircle className="w-3 h-3" /> Draft</span>;
    }
  };

  const getStageLabel = (s: Shipment) => {
    if (s.status === 'COMPLETED') return 'Stage 4: Shipment Fully Executed';
    if (s.products && s.products.length > 0) return `Stage 3: ${s.products.length} Products Configured & Duties Calculated`;
    return 'Stage 2: Customer Requirements & Supplier RFQ Studio';
  };

  return (
    <div className="space-y-6 font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
        <div>
          <h1 className="text-xl font-black text-slate-900 flex items-center gap-2">
            <Ship className="w-6 h-6 text-blue-600" />
            Shipments & Operations Hub
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Seamlessly initialize shipment pipelines, record requirements, allocate vendors, and auto-resume where you left off.
          </p>
        </div>

        <button
          onClick={() => {
            setWizardResumeState(null);
            setShowWizardModal(true);
          }}
          className="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition-all shadow-sm flex items-center gap-2 cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>New Shipment Pipeline</span>
        </button>
      </div>

      {/* ⚡ Quick Resume In-Progress Shipment Banner */}
      {!loading && inProgressShipment && (
        <div className="bg-gradient-to-r from-slate-900 via-blue-950 to-slate-900 text-white p-5 rounded-2xl border border-blue-800/60 shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-amber-500/20 border border-amber-400/40 rounded-2xl flex items-center justify-center shrink-0">
              <Zap className="w-6 h-6 text-amber-400 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2 text-[11px] font-mono font-bold text-blue-300 uppercase tracking-wider">
                <span>Active Work-In-Progress Shipment</span>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              </div>
              <h3 className="text-base font-black text-white mt-0.5">
                Shipment #{inProgressShipment.shipment_no} ({inProgressShipment.shipment_date || 'Draft Date'})
              </h3>
              <p className="text-xs text-slate-300 flex items-center gap-1.5 mt-0.5">
                <Layers className="w-3.5 h-3.5 text-blue-400" />
                <span>{getStageLabel(inProgressShipment)}</span>
              </p>
            </div>
          </div>

          <button
            onClick={() => handleResumeShipment(inProgressShipment)}
            className="px-5 py-3 bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-black rounded-xl transition-all shadow-md flex items-center justify-center gap-2 cursor-pointer shrink-0"
          >
            <span>Continue Right Where You Left Off</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Shipments List */}
      {loading ? (
        <div className="p-12 text-center text-xs text-slate-500 font-medium">Loading shipments...</div>
      ) : shipments.length === 0 ? (
        <div className="bg-white p-12 rounded-2xl border border-slate-200 text-center space-y-3">
          <Ship className="w-12 h-12 text-slate-300 mx-auto" />
          <h3 className="text-sm font-bold text-slate-700">No Shipments Found</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Click <span className="font-semibold text-blue-600">New Shipment Pipeline</span> to create your first shipment.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {shipments.map(s => (
            <div
              key={s.id}
              onClick={() => handleResumeShipment(s)}
              className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs hover:shadow-md hover:border-blue-400 cursor-pointer transition-all space-y-3 flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-sm font-black text-blue-900">{s.shipment_no}</span>
                  {getStatusBadge(s.status)}
                </div>

                <div className="text-xs text-slate-600 font-medium space-y-1.5 bg-slate-50/70 p-3 rounded-xl border border-slate-100">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                    <span>Date: <strong className="text-slate-800">{s.shipment_date || 'N/A'}</strong></span>
                  </div>
                  <div className="text-slate-500">
                    Customers: <strong className="text-slate-800 font-semibold">{s.customers?.map(c => c.name).join(', ') || 'None'}</strong>
                  </div>
                  <div className="text-blue-700 font-bold flex items-center gap-1 pt-0.5">
                    <Layers className="w-3.5 h-3.5 text-blue-500" />
                    <span>{getStageLabel(s)}</span>
                  </div>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-blue-700 font-bold">
                <span>Resume Stage →</span>
                <ChevronRight className="w-4 h-4" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Shipment Wizard Modal */}
      {showWizardModal && (
        <ShipmentWizardModal
          initialShipmentId={wizardResumeState?.shipmentId}
          initialStep={wizardResumeState?.step}
          onClose={() => {
            setShowWizardModal(false);
            setWizardResumeState(null);
          }}
          onSelectShipment={(id) => onSelectShipment(id)}
        />
      )}
    </div>
  );
};

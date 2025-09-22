// Types for maintenance service
export type AlertLevel = 'low' | 'medium' | 'high' | 'critical';
export type OrderStatus = 'open' | 'assigned' | 'in_progress' | 'completed' | 'cancelled';

export interface WorkOrder {
  id: string;
  title: string;
  description: string;
  priority: AlertLevel;
  status: OrderStatus;
  location: string;
  assigned_team?: string;
  created_at: string;
  updated_at: string;
  estimated_duration: number;
}

export interface Team {
  id: string;
  name: string;
  status: 'disponivel' | 'ocupado';
  members_count: number;
  description?: string;
  specialization?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ServiceOrderUpdate {
  title?: string;
  description?: string;
  priority?: AlertLevel;
  location?: string;
  status?: OrderStatus;
}
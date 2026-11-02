export type UserRole =
  | 'super_admin'
  | 'sem'
  | 'swe'
  | 'ssm'
  | 'directeur_campus'
  | 'directeur_technique';

export interface User {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone_number?: string;
  role: UserRole;
  status: 'active' | 'invited' | 'disabled';
  created_at: string;
}

export interface Camp {
  id: string;
  organizer_id: string;
  name: string;
  slug: string;
  description?: string;
  start_date: string;
  end_date: string;
  city?: string;
  age?: number;
  capacity: number;
  price: number;
  status: 'draft' | 'published' | 'archived';
  created_at: string;
  modalities?: Modality[];
  registration_count?: number;
}

export interface Modality {
  id: string;
  type: 'age_restriction' | 'education_level' | 'other';
  label: string;
}

export interface Registration {
  id: string;
  camp_id: string;
  first_name: string;
  last_name: string;
  email: string;
  comment?: string;
  confirmed: boolean;
  created_at: string;
}

export interface Payment {
  id: string;
  registration_id: string;
  amount_total: number;
  platform_fee: number;
  organizer_amount: number;
  status: 'pending' | 'success' | 'failed';
  transaction_id?: string;
}

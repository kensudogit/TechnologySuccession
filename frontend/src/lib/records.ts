export type MaintenanceRecord = {
  id: string;
  equipment_name?: string;
  equipment_id?: string;
  line_name?: string;
  event_date?: string;
  record_category?: string;
  symptom?: string;
  root_cause?: string;
  action_taken?: string;
  measured_value?: string;
  unit?: string;
  result?: string;
  inspector?: string;
  source_file?: string;
  source_type?: string;
};

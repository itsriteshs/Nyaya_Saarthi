import { apiRequest } from "./client";

export interface DatasetMetadata { name: string; format: string; rows: number; columns: number }
export interface DatasetSummary { dataset_count: number; datasets: DatasetMetadata[] }
export interface ValidationSummary {
  status: "not_run" | "completed";
  last_audit: string | null;
  critical_errors?: number;
  warnings?: number;
  file_count?: number;
  datasets?: Array<{ name: string; rows: number }>;
}
export function healthCheck() {
  return apiRequest<{ status: string; service: string; version: string }>("/api/v1/health");
}
export function getDatasetSummary() {
  return apiRequest<DatasetSummary>("/api/v1/datasets/summary");
}
export function getDatasetValidation() {
  return apiRequest<ValidationSummary>("/api/v1/datasets/validation");
}

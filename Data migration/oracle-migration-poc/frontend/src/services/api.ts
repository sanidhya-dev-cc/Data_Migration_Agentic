import axios from 'axios';
import {
  DatabaseConfig,
  MigrationResponse,
  SchemaAnalysis,
  ValidationResult,
  TableInfo
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const discoveryApi = {
  testConnection: async (dbConfig: DatabaseConfig) => {
    const response = await api.post('/api/discovery/test-connection', dbConfig);
    return response.data;
  },

  listDatabases: async () => {
    const response = await api.get('/api/discovery/databases');
    return response.data;
  },
};

export const schemaApi = {
  analyzeSchema: async (dbConfig: DatabaseConfig): Promise<SchemaAnalysis> => {
    const response = await api.post('/api/schema/analyze', dbConfig);
    return response.data;
  },

  getSourceSchema: async (dbId: string) => {
    const response = await api.get(`/api/schema/source/${dbId}`);
    return response.data;
  },

  getTargetSchema: async (dbId: string) => {
    const response = await api.get(`/api/schema/target/${dbId}`);
    return response.data;
  },

  compareSchemas: async (sourceConfig: DatabaseConfig, targetConfig: DatabaseConfig) => {
    const response = await api.post('/api/schema/compare', {
      source_config: sourceConfig,
      target_config: targetConfig,
    });
    return response.data;
  },
};

export const migrationApi = {
  startMigration: async (request: {
    migration_name: string;
    source_db: DatabaseConfig;
    intermediate_db?: DatabaseConfig;
    target_db: DatabaseConfig;
    tables: TableInfo[];
    migration_mode: string;
    business_priority: string;
    max_downtime_minutes: number;
    user_notes?: string;
  }): Promise<MigrationResponse> => {
    const response = await api.post('/api/migration/start', request);
    return response.data;
  },

  getMigrationStatus: async (migrationId: string): Promise<MigrationResponse> => {
    const response = await api.get(`/api/migration/${migrationId}/status`);
    return response.data;
  },

  approveMigration: async (
    migrationId: string,
    approved: boolean,
    comments?: string,
    approver?: string
  ) => {
    const response = await api.post(`/api/migration/${migrationId}/approve`, {
      migration_id: migrationId,
      approved,
      comments,
      approver: approver || 'user',
    });
    return response.data;
  },

  cancelMigration: async (migrationId: string) => {
    const response = await api.post(`/api/migration/${migrationId}/cancel`);
    return response.data;
  },
};

export const validationApi = {
  getValidationResult: async (migrationId: string): Promise<ValidationResult> => {
    const response = await api.get(`/api/validation/${migrationId}`);
    return response.data;
  },

  reconcileValidation: async (migrationId: string) => {
    const response = await api.post(`/api/validation/${migrationId}/reconcile`);
    return response.data;
  },
};

export default api;

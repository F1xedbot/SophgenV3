import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1', // Proxy will handle this in dev, relative path in prod
});

export const getInjections = (limit, offset, func_name, ref_hash) => api.get('/db/injections', { params: { limit, offset, func_name, ref_hash } });
export const getInjectionById = (id) => api.get(`/db/injections/${id}`);
export const deleteInjections = (ids) => api.delete('/db/injections', { data: ids });
export const getGroupedInjections = (limit, offset, search) => api.get('/db/injections/grouped', { params: { limit, offset, search } });
export const getValidations = (limit, offset, func_name, ref_hash) => api.get('/db/validations', { params: { limit, offset, func_name, ref_hash } });
export const getValidationById = (id) => api.get(`/db/validations/${id}`);
export const deleteValidations = (ids) => api.delete('/db/validations', { data: ids });
export const getGroupedValidations = (limit, offset, search) => api.get('/db/validations/grouped', { params: { limit, offset, search } });
export const getResearches = (limit, offset, search) => api.get('/db/researches', { params: { limit, offset, search } });
export const getResearchById = (id) => api.get(`/db/researches/${id}`);
export const getCondensed = (limit, offset, search) => api.get('/db/condensed', { params: { limit, offset, search } });
export const getCondensedById = (id) => api.get(`/db/condensed/${id}`);
export const getStats = () => api.get('/db/stats');

export const generateResearch = (data) => api.post('/generation/research', data);
export const generateInjection = (data) => api.post('/generation/injection', data);
export const generateValidation = (data) => api.post('/generation/validation', data);
export const getSample = () => api.get('/generation/sample');

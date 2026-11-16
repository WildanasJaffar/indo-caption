import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const projectApi = {
  uploadVideo: (formData, onUploadProgress) =>
    api.post('/projects/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress,
    }),
  registerLocal: (filePath, name) =>
    api.post('/projects/register-local', { file_path: filePath, name }),
  list: () => api.get('/projects'),
  get: (id) => api.get(`/projects/${id}`),
  delete: (id) => api.delete(`/projects/${id}`),
};

export const transcribeApi = {
  getHardware: () => api.get('/transcribe/hardware'),
  start: (projectId, modelSize = 'small', language = 'id') =>
    api.post(`/transcribe/${projectId}?model_size=${modelSize}&language=${language}`),
};

export const subtitleApi = {
  list: (projectId) => api.get(`/subtitles/${projectId}`),
  create: (projectId, data) => {
    let url = `/subtitles/${projectId}?start_time=${data.startTime}&end_time=${data.endTime}&text=${encodeURIComponent(data.text || '')}`;
    if (data.insertAfterId) {
      url += `&insert_after_id=${data.insertAfterId}`;
    }
    return api.post(url);
  },
  update: (subtitleId, data) => api.put(`/subtitles/${subtitleId}`, data),
  delete: (subtitleId) => api.delete(`/subtitles/${subtitleId}`),
  split: (projectId, data) => api.post(`/subtitles/${projectId}/split`, data),
  merge: (projectId, data) => api.post(`/subtitles/${projectId}/merge`, data),
  resegment: (projectId, data) => api.post(`/subtitles/${projectId}/resegment`, data),
  reorder: (projectId, subtitleIds) => api.post(`/subtitles/${projectId}/reorder`, { subtitle_ids: subtitleIds }),
  swap: (projectId, subId1, subId2) => api.post(`/subtitles/${projectId}/swap`, { subtitle_id_1: subId1, subtitle_id_2: subId2 }),
  sortByTime: (projectId) => api.post(`/subtitles/${projectId}/sort-by-time`),
  timeShift: (projectId, offsetSeconds) => api.post(`/subtitles/${projectId}/time-shift`, { offset_seconds: offsetSeconds }),
};

export const exportApi = {
  startRenderVideo: (projectId, style) =>
    api.post(`/export/${projectId}/render-video`, { style }),
  getSrtUrl: (projectId) => `/api/export/${projectId}/srt`,
  getSrtWordsUrl: (projectId) => `/api/export/${projectId}/srt-words`,
  getVttUrl: (projectId) => `/api/export/${projectId}/vtt`,
  getTxtUrl: (projectId) => `/api/export/${projectId}/txt`,
  getAssUrl: (projectId) => `/api/export/${projectId}/ass`,
  getDownloadRenderUrl: (projectId, filename) => `/api/export/${projectId}/download-rendered/${filename}`,
};

export default api;


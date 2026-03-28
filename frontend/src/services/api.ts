import axios from 'axios';

const API_URL = "http://localhost:5000";

const api = axios.create({
    baseURL: API_URL
});

export const analyzeImage = async (file: File) => {
    const formData = new FormData();
    formData.append("file", file); // Key as requested: "file"

    const res = await api.post(`/analyze`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
    return res.data;
};

// Also provide stegoApi.analyze if it's needed by existing code
export const stegoApi = {
    analyze: (formData: FormData) => api.post('/analyze', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    })
};

export default api;

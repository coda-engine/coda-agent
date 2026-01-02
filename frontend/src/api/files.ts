const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface FileUploadResponse {
    filename: string;
    content_type: string;
    content: string;
    size: number;
}

export const uploadFile = async (file: File): Promise<FileUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_URL}/api/v1/files/upload`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        let errorMessage = response.statusText;
        try {
            const errorData = await response.json();
            if (errorData.detail) {
                errorMessage = errorData.detail;
            }
        } catch (e) {
            // Ignore JSON parse error
        }
        throw new Error(`Upload failed: ${errorMessage}`);
    }

    return response.json();
};

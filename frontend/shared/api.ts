// types
export interface SummaryPoint {
  title: string;
  summary: string;
  details: string;
}

export interface FileInfo {
  file_name: string;
  title?: string;
  points?: SummaryPoint[];
}

export interface UploadResponse {
  success: boolean;
  files?: FileInfo[];
  error?: string;
}

// API Base
function getFlaskApiBase(): string {
  if (typeof window !== 'undefined') {
    return (import.meta as any).env?.VITE_FLASK_API_BASE || "http://127.0.0.1:5000";
  }
  return "http://127.0.0.1:5000";
}

// Upload function
export async function uploadFileToFlask(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch(`${getFlaskApiBase()}/api/upload`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `Upload failed with status: ${response.status}`);
    }

    const data: UploadResponse = await response.json();
    if (!data.success) {
      throw new Error(data.error || "Upload failed");
    }

    return data;
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "Upload failed",
    };
  }
}

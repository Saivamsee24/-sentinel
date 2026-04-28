const DEFAULT_API_URL = "https://sentinel-fraud-api-pxak.onrender.com";
const REQUEST_TIMEOUT_MS = 40000;

const API_URL =
  import.meta.env.VITE_API_URL && String(import.meta.env.VITE_API_URL).trim().length > 0
    ? String(import.meta.env.VITE_API_URL)
    : DEFAULT_API_URL;

export type TransactionPayload = {
  transaction_id: string;
  amount: number;
  customer_id: string;
  merchant_id: string;
  features: Record<string, string | number | boolean>;
};

export type HealthResponse = {
  status: string;
  model_loaded: boolean;
  model_version: string;
};

export type TopFeature = {
  name: string;
  importance: number;
  value: string | number | boolean | null;
};

export type PredictResponse = {
  transaction_id: string;
  fraud_score: number;
  is_fraud: boolean;
  threshold: number;
  top_features: TopFeature[];
  model_version: string;
};

export type InvestigationData = {
  verdict: string;
  confidence: number;
  summary: string;
  reasoning: string[];
  recommended_action: string;
};

export type InvestigationResponse = {
  prediction: PredictResponse;
  investigation: InvestigationData;
};

export class ApiRequestError extends Error {
  constructor(message: string, public readonly status?: number) {
    super(message);
    this.name = "ApiRequestError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {}),
      },
      signal: controller.signal,
    });

    const raw = (await response.text()) || "{}";
    const data = JSON.parse(raw) as unknown;

    if (!response.ok) {
      const message =
        typeof data === "object" &&
        data !== null &&
        "detail" in data &&
        typeof (data as { detail?: unknown }).detail === "string"
          ? (data as { detail: string }).detail
          : `API request failed with status ${response.status}.`;
      throw new ApiRequestError(message, response.status);
    }

    return data as T;
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiRequestError(
        "The request timed out while waiting for the API response."
      );
    }

    if (error instanceof ApiRequestError) {
      throw error;
    }

    throw new ApiRequestError("Network error. Please check your connection and try again.");
  } finally {
    window.clearTimeout(timeoutId);
  }
}

export function getHealth() {
  return request<HealthResponse>("/health", { method: "GET" });
}

export function predictTransaction(payload: TransactionPayload) {
  return request<PredictResponse>("/predict", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function investigateTransaction(
  payload: TransactionPayload
): Promise<InvestigationResponse> {
  const raw = await request<{
    prediction: PredictResponse;
    investigation: string;
  }>("/investigate", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  let parsedInvestigation: InvestigationData;

  try {
    parsedInvestigation = JSON.parse(raw.investigation) as InvestigationData;
  } catch {
    throw new ApiRequestError("Received an invalid investigator report from the API.");
  }

  return {
    prediction: raw.prediction,
    investigation: parsedInvestigation,
  };
}

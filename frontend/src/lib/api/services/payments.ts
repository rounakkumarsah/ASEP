/**
 * ASEP — Razorpay Payments API Service
 *
 * Communicates with the FastAPI payments router.
 * The KEY_SECRET is never present in this file or any frontend code.
 */

import { apiClient } from "../client";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface CreateOrderPayload {
  /** Amount in paise (smallest INR unit). e.g. 49900 = ₹499 */
  amount: number;
  currency?: string;
  description?: string;
  notes?: Record<string, string>;
}

export interface CreateOrderResponse {
  order_id: string;
  amount: number;
  currency: string;
  /** Public key — safe to pass directly to Razorpay Checkout */
  key_id: string;
}

export interface VerifyPaymentPayload {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
}

export interface VerifyPaymentResponse {
  success: boolean;
  payment_id: string;
  message: string;
}

export interface PaymentRecord {
  id: string;
  razorpay_order_id: string;
  razorpay_payment_id: string | null;
  amount: number;
  currency: string;
  status: "created" | "authorized" | "captured" | "failed" | "refunded";
  description: string | null;
}

// ---------------------------------------------------------------------------
// API calls
// ---------------------------------------------------------------------------

/**
 * Create a Razorpay order on the backend.
 * Returns the order ID and the PUBLIC key_id to initialise Checkout.
 */
export async function createOrder(
  payload: CreateOrderPayload
): Promise<CreateOrderResponse> {
  const response = await apiClient.post<CreateOrderResponse>(
    "/api/v1/payments/create-order",
    payload
  );
  return response.data;
}

/**
 * Send the three Razorpay callback values to the backend for HMAC verification.
 * The backend confirms authenticity before marking the payment as captured.
 */
export async function verifyPayment(
  payload: VerifyPaymentPayload
): Promise<VerifyPaymentResponse> {
  const response = await apiClient.post<VerifyPaymentResponse>(
    "/api/v1/payments/verify",
    payload
  );
  return response.data;
}

/**
 * Fetch the current user's payment history.
 */
export async function getPaymentHistory(
  limit = 20
): Promise<PaymentRecord[]> {
  const response = await apiClient.get<PaymentRecord[]>(
    `/api/v1/payments/history?limit=${limit}`
  );
  return response.data;
}

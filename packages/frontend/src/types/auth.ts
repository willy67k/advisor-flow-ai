/** Response from ``GET /api/auth/me/`` (DJango / DRF). */
export interface MeResponse {
  id: number;
  username: string;
  email: string;
  role: string;
}

export interface TokenPairResponse {
  access: string;
  refresh: string;
}

export interface RegisterResponse extends TokenPairResponse {
  user: MeResponse;
}

export interface RegisterRequestBody {
  username: string;
  email: string;
  password: string;
  password_confirm: string;
}

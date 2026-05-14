export interface Client {
  readonly id: number;
  readonly name: string;
  readonly email: string;
  readonly phone: string;
  readonly advisor: number;
}

export interface ClientInput {
  name: string;
  email: string;
  phone: string;
}

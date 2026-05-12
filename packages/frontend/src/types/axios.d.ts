import "axios";

declare module "axios" {
  interface AxiosRequestConfig {
    /** Used to avoid infinite 401 retry loops inside the refresh interceptor. */
    _retry?: boolean;
  }
}

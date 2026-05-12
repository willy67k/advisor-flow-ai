import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";

import { fetchMe, registerRequest } from "../../services/api";

const schema = z
  .object({
    username: z.string().min(1, "Username required").max(150),
    email: z.string().email("Valid email required").min(1),
    password: z.string().min(8, "At least 8 characters"),
    password_confirm: z.string().min(1, "Confirm your password"),
  })
  .superRefine((data, ctx) => {
    if (data.password !== data.password_confirm) {
      ctx.addIssue({
        code: "custom",
        path: ["password_confirm"],
        message: "Passwords do not match",
      });
    }
  });

type FormValues = z.infer;

export function RegisterPage() {
  const navigate = useNavigate();
  const [formError, setFormError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  async function onSubmit(values: FormValues) {
    setFormError(null);
    try {
      await registerRequest({
        username: values.username,
        email: values.email,
        password: values.password,
        password_confirm: values.password_confirm,
      });
      await fetchMe();
      navigate("/dashboard", { replace: true });
    } catch (err: unknown) {
      if (axiosIsValidationError(err)) {
        setFormError(formatServerErrors(err.response.data));
      } else {
        setFormError("We couldn’t create your account. Try a different username or email.");
      }
    }
  }

  return (
    <div className="flex min-h-screen flex-col justify-center bg-slate-950 px-4 pb-24">
      <div className="mx-auto w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900/80 p-8 shadow-xl shadow-black/40">
        <p className="text-xs tracking-[0.25em] text-slate-500 uppercase">AdvisorFlow AI</p>
        <h1 className="mt-2 text-2xl font-semibold text-white">Create your account</h1>
        <p className="mt-2 text-sm leading-relaxed text-slate-400">Set up an advisor profile to access the workspace. Use a strong password you don’t reuse elsewhere.</p>

        <form className="mt-8 flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-slate-400" htmlFor="reg-username">
              Username
            </label>
            <input id="reg-username" autoComplete="username" className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white ring-emerald-500/40 outline-none focus:ring-2" {...register("username")} />
            {errors.username ? <p className="text-xs text-rose-400">{errors.username.message}</p> : null}
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-slate-400" htmlFor="reg-email">
              Email
            </label>
            <input id="reg-email" type="email" autoComplete="email" className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white ring-emerald-500/40 outline-none focus:ring-2" {...register("email")} />
            {errors.email ? <p className="text-xs text-rose-400">{errors.email.message}</p> : null}
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-slate-400" htmlFor="reg-password">
              Password
            </label>
            <input
              id="reg-password"
              type="password"
              autoComplete="new-password"
              className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white ring-emerald-500/40 outline-none focus:ring-2"
              {...register("password")}
            />
            {errors.password ? <p className="text-xs text-rose-400">{errors.password.message}</p> : null}
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-slate-400" htmlFor="reg-password2">
              Confirm password
            </label>
            <input
              id="reg-password2"
              type="password"
              autoComplete="new-password"
              className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white ring-emerald-500/40 outline-none focus:ring-2"
              {...register("password_confirm")}
            />
            {errors.password_confirm ? <p className="text-xs text-rose-400">{errors.password_confirm.message}</p> : null}
          </div>
          {formError ? <p className="text-sm whitespace-pre-line text-rose-400">{formError}</p> : null}
          <button className="mt-2 flex items-center justify-center rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-emerald-950 transition hover:bg-emerald-400 disabled:opacity-50" disabled={isSubmitting} type="submit">
            {isSubmitting ? "Creating account…" : "Create account"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-slate-500">
          Already have an account?{" "}
          <Link className="cursor-pointer font-medium text-emerald-400 hover:text-emerald-300" to="/login">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}

function axiosIsValidationError(err: unknown): err is { response: { data: unknown; status?: number } } {
  return typeof err === "object" && err !== null && "response" in err && typeof (err as { response?: { status?: number } }).response?.status === "number" && (err as { response: { status: number } }).response.status === 400;
}

function formatServerErrors(data: unknown): string {
  if (typeof data !== "object" || data === null) {
    return "Something went wrong. Please check your details and try again.";
  }
  const parts: string[] = [];
  for (const [key, raw] of Object.entries(data)) {
    const label = key === "password_confirm" ? "Password confirmation" : key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, " ");
    if (Array.isArray(raw)) {
      parts.push(`${label}: ${raw.join("; ")}`);
    } else if (typeof raw === "string") {
      parts.push(`${label}: ${raw}`);
    }
  }
  return parts.length > 0 ? parts.join("\n") : "We couldn’t save your registration. Try again.";
}

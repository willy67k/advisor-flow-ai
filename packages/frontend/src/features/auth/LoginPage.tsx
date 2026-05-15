import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";

import { fetchMe, loginRequest } from "../../services/api";

const schema = z.object({
  username: z.string().min(1, "Username required"),
  password: z.string().min(1, "Password required"),
});

type FormValues = z.infer<typeof schema>;

export function LoginPage() {
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
      await loginRequest(values.username, values.password);
      await fetchMe();
      navigate("/dashboard", { replace: true });
    } catch {
      setFormError("We couldn’t sign you in. Check your username and password, then try again.");
    }
  }

  return (
    <div className="flex min-h-screen flex-col justify-center bg-slate-950 px-4 pb-24">
      <div className="mx-auto w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900/80 p-8 shadow-xl shadow-black/40">
        <p className="text-xs tracking-[0.25em] text-slate-500 uppercase">AdvisorFlow AI</p>
        <h1 className="mt-2 text-2xl font-semibold text-white">Welcome back</h1>
        <p className="mt-2 text-sm leading-relaxed text-slate-400">Sign in to continue to your advisor workspace.</p>

        <form className="mt-8 flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-slate-400" htmlFor="username">
              Username
            </label>
            <input
              id="username"
              autoComplete="username"
              className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white ring-emerald-500/40 outline-none placeholder:text-slate-600 focus:ring-2"
              {...register("username")}
            />
            {errors.username ? <p className="text-xs text-rose-400">{errors.username.message}</p> : null}
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-slate-400" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white ring-emerald-500/40 outline-none focus:ring-2"
              {...register("password")}
            />
            {errors.password ? <p className="text-xs text-rose-400">{errors.password.message}</p> : null}
          </div>
          {formError ? <p className="text-sm text-rose-400">{formError}</p> : null}
          <button className="mt-2 flex items-center justify-center rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-emerald-950 transition hover:bg-emerald-400 disabled:opacity-50" disabled={isSubmitting} type="submit">
            {isSubmitting ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-slate-500">
          New here?{" "}
          <Link className="cursor-pointer font-medium text-emerald-400 hover:text-emerald-300" to="/register">
            Create an account
          </Link>
        </p>
      </div>
    </div>
  );
}

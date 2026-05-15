import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { useCreateClient, useUpdateClient } from "../../hooks/useClients";
import type { Client } from "../../types/clients";

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  email: z.string().email("Valid email required"),
  phone: z.string().min(1, "Phone is required"),
});

type FormValues = z.infer<typeof schema>;

interface Props {
  readonly editTarget: Client | null;
  readonly onClose: () => void;
}

export function ClientModal({ editTarget, onClose }: Props) {
  const isEdit = editTarget !== null;
  const createMut = useCreateClient();
  const updateMut = useUpdateClient();
  const busy = createMut.isPending || updateMut.isPending;

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  useEffect(() => {
    if (editTarget) {
      reset({ name: editTarget.name, email: editTarget.email, phone: editTarget.phone });
    } else {
      reset({ name: "", email: "", phone: "" });
    }
  }, [editTarget, reset]);

  async function onSubmit(values: FormValues) {
    if (isEdit && editTarget) {
      await updateMut.mutateAsync({ id: editTarget.id, body: values });
    } else {
      await createMut.mutateAsync(values);
    }
    onClose();
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
        <h2 className="text-base font-semibold text-slate-100">{isEdit ? "Edit client" : "Add client"}</h2>
        <p className="mt-1 text-xs text-slate-500">{isEdit ? "Update client details." : "Create a new client record."}</p>

        <form className="mt-5 flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-slate-400" htmlFor="client-name">
              Full name
            </label>
            <input id="client-name" className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white ring-emerald-500/40 outline-none focus:ring-2" placeholder="Jane Smith" {...register("name")} />
            {errors.name ? <p className="text-xs text-rose-400">{errors.name.message}</p> : null}
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-slate-400" htmlFor="client-email">
              Email
            </label>
            <input
              id="client-email"
              type="email"
              className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white ring-emerald-500/40 outline-none focus:ring-2"
              placeholder="jane@example.com"
              {...register("email")}
            />
            {errors.email ? <p className="text-xs text-rose-400">{errors.email.message}</p> : null}
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-slate-400" htmlFor="client-phone">
              Phone
            </label>
            <input id="client-phone" className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white ring-emerald-500/40 outline-none focus:ring-2" placeholder="+1 555 000 0000" {...register("phone")} />
            {errors.phone ? <p className="text-xs text-rose-400">{errors.phone.message}</p> : null}
          </div>

          {(createMut.error ?? updateMut.error) ? <p className="text-sm text-rose-400">Something went wrong. Please try again.</p> : null}

          <div className="flex justify-end gap-3 pt-2">
            <button className="rounded-lg border border-slate-600 px-4 py-2 text-sm font-medium text-slate-300 hover:border-slate-500 hover:bg-slate-800" disabled={busy} type="button" onClick={onClose}>
              Cancel
            </button>
            <button className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-emerald-950 transition hover:bg-emerald-400 disabled:opacity-50" disabled={busy} type="submit">
              {busy ? "Saving…" : isEdit ? "Save changes" : "Add client"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

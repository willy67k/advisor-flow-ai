import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { useClients } from "../../hooks/useClients";
import { useCreateMeeting, useUpdateMeeting } from "../../hooks/useMeetings";
import type { Meeting } from "../../types/meetings";

const schema = z.object({
  title: z.string().min(1, "Title is required"),
  date: z.string().min(1, "Date is required"),
  notes: z.string(),
  client: z.number({ invalid_type_error: "Select a client" }).int().positive("Select a client"),
});

type FormValues = z.infer;

interface Props {
  readonly editTarget: Meeting | null;
  readonly onClose: () => void;
}

export function MeetingModal({ editTarget, onClose }: Props) {
  const isEdit = editTarget !== null;
  const createMut = useCreateMeeting();
  const updateMut = useUpdateMeeting();
  const { data: clients, status: clientsStatus } = useClients();
  const busy = createMut.isPending || updateMut.isPending;

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  useEffect(() => {
    if (editTarget) {
      reset({
        title: editTarget.title,
        date: editTarget.date,
        notes: editTarget.notes,
        client: editTarget.client,
      });
    } else {
      reset({ title: "", date: new Date().toISOString().split("T")[0], notes: "", client: 0 });
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
      <div className="w-full max-w-lg rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
        <h2 className="text-base font-semibold text-slate-100">{isEdit ? "Edit meeting" : "New meeting"}</h2>
        <p className="mt-1 text-xs text-slate-500">{isEdit ? "Update meeting details." : "Create a meeting record for a client."}</p>

        <form className="mt-5 flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-slate-400" htmlFor="meeting-title">
              Title
            </label>
            <input id="meeting-title" className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white ring-emerald-500/40 outline-none focus:ring-2" placeholder="Q3 Portfolio Review" {...register("title")} />
            {errors.title ? <p className="text-xs text-rose-400">{errors.title.message}</p> : null}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-slate-400" htmlFor="meeting-date">
                Date
              </label>
              <input id="meeting-date" type="date" className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white ring-emerald-500/40 outline-none focus:ring-2" {...register("date")} />
              {errors.date ? <p className="text-xs text-rose-400">{errors.date.message}</p> : null}
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-slate-400" htmlFor="meeting-client">
                Client
              </label>
              <select
                id="meeting-client"
                className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 ring-emerald-500/40 outline-none focus:ring-2 disabled:opacity-50"
                disabled={clientsStatus === "pending"}
                {...register("client", { valueAsNumber: true })}
              >
                <option value={0}>{clientsStatus === "pending" ? "Loading…" : "Select client"}</option>
                {(clients ?? []).map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
              {errors.client ? <p className="text-xs text-rose-400">{errors.client.message}</p> : null}
            </div>
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-slate-400" htmlFor="meeting-notes">
              Notes
            </label>
            <textarea
              id="meeting-notes"
              className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white ring-emerald-500/40 outline-none placeholder:text-slate-600 focus:ring-2"
              placeholder="Discussed portfolio allocation…"
              rows={4}
              {...register("notes")}
            />
          </div>

          {createMut.error ?? updateMut.error ? <p className="text-sm text-rose-400">Something went wrong. Please try again.</p> : null}

          <div className="flex justify-end gap-3 pt-2">
            <button className="rounded-lg border border-slate-600 px-4 py-2 text-sm font-medium text-slate-300 hover:border-slate-500 hover:bg-slate-800" disabled={busy} type="button" onClick={onClose}>
              Cancel
            </button>
            <button className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-emerald-950 transition hover:bg-emerald-400 disabled:opacity-50" disabled={busy} type="submit">
              {busy ? "Saving…" : isEdit ? "Save changes" : "Create meeting"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

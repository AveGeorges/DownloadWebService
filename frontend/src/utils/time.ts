const NSK = "Asia/Novosibirsk";

export function formatNsk(iso: string | null | undefined): string {
  if (!iso) {
    return "—";
  }
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return iso;
  }
  return new Intl.DateTimeFormat("ru-RU", {
    timeZone: NSK,
    dateStyle: "short",
    timeStyle: "medium",
  }).format(date);
}

export function isJobActive(status: string): boolean {
  return status === "pending" || status === "running" || status === "waiting";
}

/**
 * Failure to sentence.
 *
 * Two audiences read an error, and they need different things. A person needs
 * to know what happened and what to do next. A developer needs the status, the
 * URL and whatever the server said. Collapsing those into one string is how
 * "Cannot reach the API at http://localhost:8000" ended up rendered inside a
 * sign-in form on production.
 *
 * So every failure carries both: `message` is shown, `detail` is logged.
 */

/** Shown when the request never reached a server at all. */
export const OFFLINE_MESSAGE =
  "Cannot reach the service right now. Check your connection and try again.";

/** Shown when the frontend was built without a backend URL. */
export const MISCONFIGURED_MESSAGE =
  "This app is not connected to a server yet. If you deployed it, set NEXT_PUBLIC_API_URL.";

/**
 * Status to sentence.
 *
 * Deliberately says what to do, not what went wrong internally. Nothing here
 * names a host, a stack frame, or an internal service.
 */
const BY_STATUS: Record<number, string> = {
  400: "That request was not valid. Check the values and try again.",
  401: "Your session has expired. Sign in again.",
  403: "You do not have access to that.",
  404: "That is not here. It may have been deleted.",
  409: "That already exists.",
  413: "That is too large to process. Try a smaller batch.",
  422: "Some values were not accepted. Check the form and try again.",
  429: "Too many requests. Wait a moment and try again.",
  500: "Something went wrong on our side. Try again in a moment.",
  502: "The service is unreachable. Try again in a moment.",
  503: "The service is temporarily unavailable. Try again in a moment.",
  504: "That took too long. Try again, or with a smaller batch.",
};

/**
 * Statuses where the server's own text is written for the person reading it.
 *
 * The backend authors these deliberately: which password rule failed, which
 * CSV column is missing, why an upload was rejected. Replacing them with a
 * generic sentence would make the product worse, not safer. Every other status
 * gets the mapped message and the server text goes to the console.
 */
const TRUST_SERVER_TEXT = new Set([400, 409, 422]);

export function messageForStatus(status: number, serverText?: string): string {
  if (status === 0) return OFFLINE_MESSAGE;

  if (TRUST_SERVER_TEXT.has(status) && serverText && serverText.trim()) {
    return serverText;
  }

  const mapped = BY_STATUS[status];
  if (mapped) return mapped;

  // Unmapped 4xx is the caller's problem, unmapped 5xx is ours. Neither
  // should show a bare status code to someone trying to sign in.
  return status >= 500
    ? "Something went wrong on our side. Try again in a moment."
    : "That did not work. Try again.";
}

/**
 * True when the app was built pointing at a developer's machine but is being
 * served from somewhere else. Always a deployment misconfiguration, never
 * something the person using it can act on, so it is logged loudly and shown
 * plainly.
 */
export function looksMisconfigured(apiBase: string): boolean {
  if (typeof window === "undefined") return false;
  const local = /^https?:\/\/(localhost|127\.0\.0\.1|\[::1\])/i;
  return local.test(apiBase) && !local.test(window.location.origin);
}

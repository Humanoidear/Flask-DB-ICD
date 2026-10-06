const API_URL = import.meta.env.VITE_API_URL ?? ""

async function request(path, options = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  })

  if (!res.ok) {
    let message = `Request failed (${res.status})`
    try {
      const data = await res.json()
      if (data.error) message = data.error
    } catch {
      // keep the default message
    }
    throw new Error(message)
  }

  if (res.status === 204) return null
  return res.json()
}

export const notesApi = {
  list: () => request("/api/notes"),
  create: (note) =>
    request("/api/notes", { method: "POST", body: JSON.stringify(note) }),
  update: (id, note) =>
    request(`/api/notes/${id}`, { method: "PUT", body: JSON.stringify(note) }),
  remove: (id) => request(`/api/notes/${id}`, { method: "DELETE" }),
}

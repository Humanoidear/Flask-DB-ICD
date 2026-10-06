import { useEffect, useMemo, useState } from "react"
import {
  Database,
  FileText,
  Loader2,
  Plus,
  Save,
  Search,
  ServerCrash,
  Trash2,
} from "lucide-react"

import { notesApi } from "@/lib/api"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"

const formatDate = (iso) =>
  new Date(iso).toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short" })

const preview = (text) => text.replace(/\s+/g, " ").trim().slice(0, 72)

export default function App() {
  const [notes, setNotes] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [draft, setDraft] = useState({ title: "", content: "" })
  const [query, setQuery] = useState("")
  const [status, setStatus] = useState("loading")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")

  const selected = useMemo(
    () => notes.find((note) => note.id === selectedId) ?? null,
    [notes, selectedId]
  )

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return notes
    return notes.filter(
      (note) =>
        note.title.toLowerCase().includes(q) ||
        note.content.toLowerCase().includes(q)
    )
  }, [notes, query])

  async function load() {
    try {
      setStatus("loading")
      const data = await notesApi.list()
      setNotes(data)
      setStatus("ready")
      setError("")
      if (data.length && selectedId == null) selectNote(data[0])
    } catch (err) {
      setError(err.message)
      setStatus("error")
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function selectNote(note) {
    setSelectedId(note.id)
    setDraft({ title: note.title, content: note.content })
    setError("")
  }

  function startNew() {
    setSelectedId(null)
    setDraft({ title: "", content: "" })
    setError("")
  }

  async function save() {
    if (!draft.title.trim()) {
      setError("A title is required before saving.")
      return
    }
    setSaving(true)
    setError("")
    try {
      if (selectedId == null) {
        const created = await notesApi.create(draft)
        await load()
        selectNote(created)
      } else {
        const updated = await notesApi.update(selectedId, draft)
        setNotes((prev) =>
          prev.map((note) => (note.id === updated.id ? updated : note))
        )
        selectNote(updated)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function remove() {
    if (selectedId == null) return
    if (!window.confirm("Delete this note?")) return
    try {
      await notesApi.remove(selectedId)
      const remaining = notes.filter((note) => note.id !== selectedId)
      setNotes(remaining)
      if (remaining.length) selectNote(remaining[0])
      else startNew()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="min-h-screen bg-muted/30">
      <header className="border-b bg-background/80 backdrop-blur sticky top-0 z-10">
        <div className="mx-auto flex max-w-6xl items-center gap-3 px-4 py-3">
          <div className="flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Database className="size-5" />
          </div>
          <div className="mr-auto">
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-semibold tracking-tight">DataNotes</h1>
              <Badge variant="secondary">Datacenters</Badge>
            </div>
            <p className="text-xs text-muted-foreground">
              React + shadcn/ui &middot; Flask REST API &middot; SQLite SGBD
            </p>
          </div>
          <ConnectionBadge status={status} />
        </div>
      </header>

      <main className="mx-auto grid max-w-6xl gap-4 px-4 py-6 md:grid-cols-[20rem_1fr]">
        <section className="flex flex-col gap-3">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search notes..."
                className="pl-8"
              />
            </div>
            <Button onClick={startNew} size="icon" title="New note">
              <Plus />
            </Button>
          </div>

          {error && (
            <p className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {error}
            </p>
          )}

          <div className="flex flex-col gap-2">
            {status === "loading" && (
              <p className="flex items-center gap-2 px-1 py-6 text-sm text-muted-foreground">
                <Loader2 className="size-4 animate-spin" /> Loading notes...
              </p>
            )}

            {status === "error" && (
              <p className="flex items-center gap-2 px-1 py-6 text-sm text-muted-foreground">
                <ServerCrash className="size-4" /> Backend unreachable.
              </p>
            )}

            {status === "ready" && filtered.length === 0 && (
              <p className="px-1 py-6 text-sm text-muted-foreground">
                {notes.length === 0
                  ? "No notes yet. Create your first one."
                  : "No notes match your search."}
              </p>
            )}

            {filtered.map((note) => (
              <Card
                key={note.id}
                onClick={() => selectNote(note)}
                className={cn(
                  "cursor-pointer gap-2 py-4 transition-colors hover:border-ring",
                  note.id === selectedId && "border-primary ring-1 ring-primary"
                )}
              >
                <div className="flex items-center gap-2 px-4">
                  <FileText className="size-4 shrink-0 text-muted-foreground" />
                  <span className="truncate text-sm font-medium">
                    {note.title}
                  </span>
                </div>
                <p className="px-4 text-xs text-muted-foreground">
                  {preview(note.content) || "Empty note"}
                </p>
                <p className="px-4 text-[11px] text-muted-foreground/70">
                  {formatDate(note.updated_at)}
                </p>
              </Card>
            ))}
          </div>
        </section>

        <Card className="gap-4 py-6">
          <div className="flex flex-col gap-4 px-6">
            <div className="grid gap-2">
              <Label htmlFor="title">Title</Label>
              <Input
                id="title"
                value={draft.title}
                onChange={(e) =>
                  setDraft({ ...draft, title: e.target.value })
                }
                placeholder="Note title"
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="content">Content</Label>
              <Textarea
                id="content"
                value={draft.content}
                onChange={(e) =>
                  setDraft({ ...draft, content: e.target.value })
                }
                placeholder="Write something about datacenters..."
                className="min-h-[22rem]"
              />
            </div>

            <div className="flex items-center gap-2">
              <Button onClick={save} disabled={saving}>
                {saving ? (
                  <Loader2 className="animate-spin" />
                ) : (
                  <Save />
                )}
                {selectedId == null ? "Create note" : "Save changes"}
              </Button>
              <Button
                variant="outline"
                onClick={startNew}
                disabled={saving}
              >
                <Plus /> New
              </Button>
              <Button
                variant="destructive"
                className="ml-auto"
                onClick={remove}
                disabled={saving || selectedId == null}
              >
                <Trash2 /> Delete
              </Button>
            </div>

            {selected && (
              <p className="text-xs text-muted-foreground">
                Created {formatDate(selected.created_at)} &middot; Updated{" "}
                {formatDate(selected.updated_at)}
              </p>
            )}
          </div>
        </Card>
      </main>
    </div>
  )
}

function ConnectionBadge({ status }) {
  if (status === "loading")
    return (
      <Badge variant="outline" className="gap-1.5">
        <Loader2 className="size-3 animate-spin" /> Connecting
      </Badge>
    )
  if (status === "error")
    return (
      <Badge variant="destructive" className="gap-1.5">
        Offline
      </Badge>
    )
  return (
    <Badge variant="outline" className="gap-1.5">
      <span className="size-2 rounded-full bg-green-500" /> API connected
    </Badge>
  )
}

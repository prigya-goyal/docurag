import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Plus, Library, FileText, X } from "lucide-react";
import toast from "react-hot-toast";
import { kbApi } from "../api/endpoints";
import type { KnowledgeBase } from "../types";
import EmptyState from "../components/EmptyState";
import { SkeletonCard } from "../components/Skeleton";
import { extractErrorMessage } from "../api/client";

export default function KnowledgeBasesPage() {
  const [kbs, setKbs] = useState<KnowledgeBase[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [creating, setCreating] = useState(false);

  function load() {
    setLoading(true);
    kbApi
      .list()
      .then((res) => setKbs(res.data))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    try {
      await kbApi.create({ name, description });
      toast.success("Knowledge base created");
      setShowModal(false);
      setName("");
      setDescription("");
      load();
    } catch (err) {
      toast.error(extractErrorMessage(err));
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="p-8 max-w-6xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-display text-3xl font-semibold text-ink-900 dark:text-ink-50">Knowledge bases</h1>
          <p className="text-sm text-ink-400 mt-1">Organize documents into collections you can ask questions about.</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 bg-ink-900 dark:bg-amber-500 text-white dark:text-ink-950 text-sm font-medium px-4 py-2.5 rounded-lg hover:opacity-90"
        >
          <Plus size={16} /> New knowledge base
        </button>
      </div>

      {loading ? (
        <div className="grid md:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : kbs.length === 0 ? (
        <EmptyState
          icon={Library}
          title="No knowledge bases yet"
          description="Create your first knowledge base to start uploading documents and asking questions."
          action={
            <button
              onClick={() => setShowModal(true)}
              className="flex items-center gap-2 bg-ink-900 dark:bg-amber-500 text-white dark:text-ink-950 text-sm font-medium px-4 py-2.5 rounded-lg hover:opacity-90"
            >
              <Plus size={16} /> New knowledge base
            </button>
          }
        />
      ) : (
        <div className="grid md:grid-cols-3 gap-4">
          {kbs.map((kb) => (
            <Link
              key={kb.id}
              to={`/knowledge-bases/${kb.id}`}
              className="rounded-xl border border-ink-200 dark:border-ink-800 bg-white dark:bg-ink-900 p-5 hover:border-amber-500/50 hover:shadow-sm transition-all"
            >
              <h3 className="font-display font-semibold text-lg mb-1 truncate">{kb.name}</h3>
              <p className="text-xs text-ink-400 line-clamp-2 mb-4 min-h-[2rem]">{kb.description || "No description"}</p>
              <div className="flex items-center justify-between text-xs text-ink-400">
                <span className="flex items-center gap-1.5">
                  <FileText size={12} /> {kb.document_count} document{kb.document_count === 1 ? "" : "s"}
                </span>
                <span>{new Date(kb.updated_at).toLocaleDateString()}</span>
              </div>
            </Link>
          ))}
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 px-4" onClick={() => setShowModal(false)}>
          <div
            className="bg-white dark:bg-ink-900 rounded-2xl p-6 w-full max-w-sm border border-ink-200 dark:border-ink-800"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display text-lg font-semibold">New knowledge base</h2>
              <button onClick={() => setShowModal(false)} className="text-ink-400 hover:text-ink-900 dark:hover:text-ink-50">
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-ink-500 mb-1.5">Name</label>
                <input
                  required
                  autoFocus
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. College"
                  className="w-full px-3 py-2 rounded-lg border border-ink-200 dark:border-ink-700 bg-ink-50 dark:bg-ink-800 text-sm outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-ink-500 mb-1.5">Description</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="What's in this knowledge base?"
                  rows={3}
                  className="w-full px-3 py-2 rounded-lg border border-ink-200 dark:border-ink-700 bg-ink-50 dark:bg-ink-800 text-sm outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500 resize-none"
                />
              </div>
              <button
                type="submit"
                disabled={creating}
                className="w-full bg-ink-900 dark:bg-amber-500 text-white dark:text-ink-950 font-medium text-sm py-2.5 rounded-lg hover:opacity-90 disabled:opacity-60"
              >
                Create
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

import { Trash2 } from "lucide-react";

import { useDocuments } from "../hooks/useDocuments";

const DocumentList = () => {
	const { documents, deleteDocument } = useDocuments();

	return (
		<section className="rounded-3xl bg-white/90 p-6 shadow-xl">
			<h2 className="font-display text-xl">Document vault</h2>
			<p className="text-sm text-black/60">Manage your indexed assets.</p>
			<div className="mt-4 space-y-3">
				{documents.map((doc) => (
					<div key={doc.id} className="flex items-center justify-between rounded-2xl border border-black/10 px-4 py-3">
						<div>
							<p className="text-sm font-semibold">{doc.original_filename}</p>
							<p className="text-xs text-black/50">{doc.file_type} • {doc.status}</p>
						</div>
						<button
							className="rounded-full border border-black/10 p-2 text-black/60 hover:text-ember"
							onClick={() => deleteDocument(doc.id)}
						>
							<Trash2 className="h-4 w-4" />
						</button>
					</div>
				))}
				{documents.length === 0 && <p className="text-sm text-black/50">No documents yet.</p>}
			</div>
		</section>
	);
};

export default DocumentList;

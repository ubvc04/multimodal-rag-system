import { useCallback, useMemo, useState } from "react";
import { useDropzone } from "react-dropzone";
import { FileText, FileUp, Image, Sheet, Table } from "lucide-react";

import { useDocuments } from "../hooks/useDocuments";

const iconForFile = (type: string) => {
	if (type.includes("pdf") || type.includes("doc")) return <FileText className="h-5 w-5" />;
	if (type.includes("image")) return <Image className="h-5 w-5" />;
	if (type.includes("csv")) return <Table className="h-5 w-5" />;
	if (type.includes("sheet") || type.includes("excel")) return <Sheet className="h-5 w-5" />;
	return <FileUp className="h-5 w-5" />;
};

const statusColor = (status: string) => {
	switch (status) {
		case "processing":
			return "bg-sky text-white animate-pulse";
		case "indexed":
			return "bg-moss text-white";
		case "failed":
			return "bg-ember text-white";
		default:
			return "bg-black/10 text-black";
	}
};

const DocumentUpload = () => {
	const { uploadDocuments, isUploading, uploadProgress, uploadError, documents } = useDocuments();
	const [localFiles, setLocalFiles] = useState<File[]>([]);

	const onDrop = useCallback((acceptedFiles: File[]) => {
		setLocalFiles((prev) => [...prev, ...acceptedFiles]);
	}, []);

	const { getRootProps, getInputProps, isDragActive } = useDropzone({
		onDrop,
		accept: {
			"application/pdf": [".pdf"],
			"application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
			"text/plain": [".txt"],
			"image/*": [".png", ".jpg", ".jpeg"],
			"text/csv": [".csv"],
			"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
		},
	});

	const uploadAll = async () => {
		if (!localFiles.length) return;
		await uploadDocuments(localFiles);
		setLocalFiles([]);
	};

	const recentDocuments = useMemo(() => documents.slice(0, 5), [documents]);

	return (
		<section className="rounded-3xl bg-white/90 p-6 shadow-xl">
			<div className="flex items-center justify-between">
				<div>
					<h2 className="font-display text-xl">Ingest new knowledge</h2>
					<p className="text-sm text-black/60">Drop PDFs, docs, sheets, or images for indexing.</p>
				</div>
				<button
					onClick={uploadAll}
					disabled={isUploading || localFiles.length === 0}
					className="rounded-full bg-ink px-4 py-2 text-xs font-semibold text-white"
				>
					{isUploading ? "Uploading..." : "Upload"}
				</button>
			</div>
			<div
				{...getRootProps()}
				className={`mt-6 rounded-2xl border-2 border-dashed p-6 text-center transition ${
					isDragActive ? "border-ember bg-ember/10" : "border-black/10"
				}`}
			>
				<input {...getInputProps()} />
				<p className="text-sm text-black/60">Drag files here, or click to browse</p>
			</div>
			{isUploading && (
				<div className="mt-4">
					<div className="flex items-center justify-between text-xs text-black/60">
						<span>Uploading...</span>
						<span>{uploadProgress}%</span>
					</div>
					<div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-black/10">
						<div
							className="h-full rounded-full bg-ember transition-all"
							style={{ width: `${uploadProgress}%` }}
						/>
					</div>
				</div>
			)}
			{uploadError && <p className="mt-3 text-sm text-ember">{uploadError}</p>}
			{localFiles.length > 0 && (
				<div className="mt-4 space-y-2">
					{localFiles.map((file) => (
						<div key={file.name} className="flex items-center justify-between rounded-xl bg-black/5 px-3 py-2">
							<div className="flex items-center gap-2 text-sm">
								{iconForFile(file.type)}
								<span>{file.name}</span>
							</div>
							<span className="text-xs text-black/50">Queued</span>
						</div>
					))}
				</div>
			)}
			<div className="mt-6">
				<h3 className="text-xs uppercase tracking-wide text-black/40">Recent documents</h3>
				<div className="mt-3 space-y-2">
					{recentDocuments.map((doc) => (
						<div key={doc.id} className="flex items-center justify-between rounded-xl bg-black/5 px-3 py-2">
							<div className="flex items-center gap-2 text-sm">
								{iconForFile(doc.file_type)}
								<span>{doc.original_filename}</span>
							</div>
							<span className={`rounded-full px-2 py-1 text-xs ${statusColor(doc.status)}`}>{doc.status}</span>
						</div>
					))}
					{recentDocuments.length === 0 && (
						<p className="text-sm text-black/50">No documents uploaded yet.</p>
					)}
				</div>
			</div>
		</section>
	);
};

export default DocumentUpload;

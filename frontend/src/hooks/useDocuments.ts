import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../lib/api";
import type { Document, DocumentListResponse } from "../types";

export const useDocuments = () => {
	const queryClient = useQueryClient();
	const [uploadProgress, setUploadProgress] = useState(0);

	const documentsQuery = useQuery({
		queryKey: ["documents"],
		queryFn: () => api.listDocuments({}),
	});

	const uploadMutation = useMutation({
		mutationFn: (files: File[]) =>
			api.uploadDocuments(files, (percent) => {
				setUploadProgress(percent);
			}),
		onMutate: () => setUploadProgress(0),
		onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents"] }),
		onSettled: () => setUploadProgress(0),
	});

	const deleteMutation = useMutation({
		mutationFn: (docId: string) => api.deleteDocument(docId),
		onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents"] }),
	});

	return {
		documents: (documentsQuery.data as DocumentListResponse | undefined)?.items ?? [],
		total: (documentsQuery.data as DocumentListResponse | undefined)?.total ?? 0,
		isLoading: documentsQuery.isLoading,
		error: documentsQuery.error,
		uploadDocuments: uploadMutation.mutateAsync,
		isUploading: uploadMutation.isPending,
		uploadProgress,
		uploadError: uploadMutation.isError ? "Upload failed" : null,
		deleteDocument: deleteMutation.mutateAsync,
	};
};

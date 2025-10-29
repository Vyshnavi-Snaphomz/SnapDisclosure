import { useState, KeyboardEvent } from "react";
import { FileInfo } from "@shared/api";
import { cn } from "@/lib/utils";

interface FileListDisplayProps {
  files: FileInfo[];
  className?: string;
  onClose?: () => void;
}

function hasExtendedContent(file: FileInfo) {
  return Boolean(
    file.fullSummary && (Array.isArray(file.fullSummary) ? file.fullSummary.length > 0 : true)
  );
}

const getDetailedSummary = (file: FileInfo): string[] => {
  if (!file.fullSummary) return ["No detailed summary available."];
  if (Array.isArray(file.fullSummary)) return file.fullSummary;
  if (typeof file.fullSummary === "string") return [file.fullSummary];
  return ["No detailed summary available."];
};

export default function FileListDisplay({ files, className, onClose }: FileListDisplayProps) {
  const [selectedFile, setSelectedFile] = useState<FileInfo | null>(null);

  const handleCardClick = (file: FileInfo) => {
    if (hasExtendedContent(file)) setSelectedFile(file);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLElement>, file: FileInfo) => {
    if ((event.key === "Enter" || event.key === " ") && hasExtendedContent(file)) {
      event.preventDefault();
      setSelectedFile(file);
    }
  };

  const closeModal = () => setSelectedFile(null);

  return (
    <div className={cn("w-full", className)}>
      <div className="rounded-3xl bg-[#f5ebe5] p-8 border border-[#f1ded4] shadow-lg">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
          <div>
            <h3 className="text-[#1a1108] text-2xl font-semibold mt-2">
              {files.length} {files.length === 1 ? "file" : "files"} uploaded
            </h3>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-semibold text-white rounded-full bg-gradient-to-r from-[#f9a66a] to-[#f46c3a] hover:from-[#fbb483] hover:to-[#f77d4c] transition-colors"
            >
              Upload Another
            </button>
          )}
        </div>

        {/* File Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {files.map((file, index) => {
            const interactive = hasExtendedContent(file);
            return (
              <article
                key={file.path || `${file.name}-${index}`}
                role={interactive ? "button" : undefined}
                tabIndex={interactive ? 0 : -1}
                onClick={() => handleCardClick(file)}
                onKeyDown={(e) => handleKeyDown(e, file)}
                className={cn(
                  "group relative rounded-2xl border bg-[#fdf7f3] p-6 shadow transition-transform duration-300",
                  interactive ? "hover:-translate-y-1 cursor-pointer" : "cursor-default"
                )}
              >
                {/* Title */}
                <h3 className="text-lg font-bold text-black mb-1">{file.title || "Untitled"}</h3>
                
                {/* Preview paragraph */}
                {file.summary && <p className="text-gray-700">{file.summary}</p>}

<br></br>
                {/* File name below title in lighter color */}
                <p className="text-gray-500 text-sm mb-2">{file.file_name}</p>    

              </article>
            );
          })}
        </div>
      </div>

      {/* Detailed Summary Modal */}
      {selectedFile && (
        <div
          className="fixed inset-0 z-40 flex items-center justify-center bg-[rgba(23,16,10,0.6)] backdrop-blur-sm px-4 py-10"
          onClick={closeModal}
        >
          <div
            className="relative w-full max-w-3xl rounded-2xl bg-[#2f2932] text-[#f7f3ed] shadow-lg overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={closeModal}
              className="absolute top-5 right-5 px-4 py-2 text-xs font-semibold text-[#f7c29c] rounded-full border hover:bg-[#3a3440]"
            >
              Close
            </button>

            <div className="px-10 py-12 space-y-6 max-h-[70vh] overflow-y-auto">
              {/* Title (bold) */}
              <h3 className="text-3xl font-bold">{selectedFile.title || "Untitled"}</h3>

              {/* File name (lighter color) */}
              <p className="text-gray-400 text-sm">{selectedFile.file_name}</p>

              {/* Detailed summary */}
              <ul className="space-y-2 text-[#f7f3ed]/90 leading-relaxed mt-4">
                {getDetailedSummary(selectedFile).map((point, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="mt-1 text-xs">-</span>
                    <span>{point}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}










// import { useState, KeyboardEvent } from "react";
// import { FileInfo } from "@shared/api";
// import { cn } from "@/lib/utils";

// interface FileListDisplayProps {
//   files: FileInfo[];
//   className?: string;
//   onClose?: () => void;
// }

// // Helper to check if a file has a detailed summary
// function hasExtendedContent(file: FileInfo) {
//   return Boolean(
//     file.fullSummary && (Array.isArray(file.fullSummary) ? file.fullSummary.length > 0 : true)
//   );
// }

// // Helper to normalize detailed summary into string array
// const getDetailedSummary = (file: FileInfo): string[] => {
//   if (!file.fullSummary) return ["No detailed summary available."];
//   if (Array.isArray(file.fullSummary)) return file.fullSummary;
//   if (typeof file.fullSummary === "string") return [file.fullSummary];
//   return ["No detailed summary available."];
// };

// export default function FileListDisplay({ files, className, onClose }: FileListDisplayProps) {
//   const [selectedFile, setSelectedFile] = useState<FileInfo | null>(null);

//   const handleCardClick = (file: FileInfo) => {
//     if (hasExtendedContent(file)) setSelectedFile(file);
//   };

//   const handleKeyDown = (event: KeyboardEvent<HTMLElement>, file: FileInfo) => {
//     if ((event.key === "Enter" || event.key === " ") && hasExtendedContent(file)) {
//       event.preventDefault();
//       setSelectedFile(file);
//     }
//   };

//   const closeModal = () => setSelectedFile(null);

//   return (
//     <div className={cn("w-full", className)}>
//       <div className="rounded-3xl bg-[#f5ebe5] p-8 border border-[#f1ded4] shadow-lg">
//         {/* Header */}
//         <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
//           <div>
//             <h3 className="text-[#1a1108] text-2xl font-semibold mt-2">
//               {files.length} {files.length === 1 ? "file" : "files"} uploaded
//             </h3>
//           </div>
//           {onClose && (
//             <button
//               onClick={onClose}
//               className="px-4 py-2 text-sm font-semibold text-white rounded-full bg-gradient-to-r from-[#f9a66a] to-[#f46c3a] hover:from-[#fbb483] hover:to-[#f77d4c] transition-colors"
//             >
//               Upload Another
//             </button>
//           )}
//         </div>

//         {/* File Cards */}
//         <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
//           {files.map((file, index) => {
//             const interactive = hasExtendedContent(file);
//             return (
//               <article
//                 key={file.path || `${file.name}-${index}`}
//                 role={interactive ? "button" : undefined}
//                 tabIndex={interactive ? 0 : -1}
//                 onClick={() => handleCardClick(file)}
//                 onKeyDown={(e) => handleKeyDown(e, file)}
//                 className={cn(
//                   "group relative rounded-2xl border bg-[#fdf7f3] p-6 shadow transition-transform duration-300",
//                   interactive ? "hover:-translate-y-1 cursor-pointer" : "cursor-default"
//                 )}
//               >
//                 {/* Title */}
//                 <h3 className="text-lg font-bold text-black mb-2">{file.title || file.name}</h3>

//                 {/* Preview paragraph */}
//                 {file.summary && <p className="text-gray-700 mb-2">{file.summary}</p>}

//                 {/* DO NOT render fullSummary here */}
//               </article>
//             );
//           })}
//         </div>
//       </div>

//       {/* Detailed Summary Modal */}
//       {selectedFile && (
//         <div
//           className="fixed inset-0 z-40 flex items-center justify-center bg-[rgba(23,16,10,0.6)] backdrop-blur-sm px-4 py-10"
//           onClick={closeModal}
//         >
//           <div
//             className="relative w-full max-w-3xl rounded-2xl bg-[#2f2932] text-[#f7f3ed] shadow-lg overflow-hidden"
//             onClick={(e) => e.stopPropagation()}
//           >
//             <button
//               onClick={closeModal}
//               className="absolute top-5 right-5 px-4 py-2 text-xs font-semibold text-[#f7c29c] rounded-full border hover:bg-[#3a3440]"
//             >
//               Close
//             </button>

//             <div className="px-10 py-12 space-y-6 max-h-[70vh] overflow-y-auto">
//               <h3 className="text-3xl font-semibold">{selectedFile.name}</h3>

//               <ul className="space-y-2 text-[#f7f3ed]/90 leading-relaxed">
//                 {getDetailedSummary(selectedFile).map((point, i) => (
//                   <li key={i} className="flex gap-2">
//                     <span className="mt-1 text-xs">-</span>
//                     <span>{point}</span>
//                   </li>
//                 ))}
//               </ul>
//             </div>
//           </div>
//         </div>
//       )}
//     </div>
//   );
// }











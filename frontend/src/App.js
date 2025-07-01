import React, { useState } from "react";
import axios from "axios";

function App() {
  const [uploadedImage, setUploadedImage] = useState(null);
  const [extractedData, setExtractedData] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) {
      setError("Please select an image file.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    setError("");
    setExtractedData({});
    setUploadedImage(URL.createObjectURL(file));

    try {
      const response = await axios.post("http://127.0.0.1:8000/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      if (response.data.error) {
        console.error("Backend error:", response.data.error);
        setError("Backend error: " + response.data.error);
      } else if (response.data.extracted_text) {
        setExtractedData(response.data.extracted_text);
      } else {
        console.error("Unexpected response:", response.data);
        setError("Extraction failed: Unexpected response structure.");
      }
    } catch (err) {
      console.error(err);
      setError("Error uploading image or extracting data.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-100 via-white to-blue-50 p-6">
      <h1 className="text-4xl font-bold text-center mb-8 text-blue-700 drop-shadow">
        Passport OCR Extractor
      </h1>

      <div className="flex justify-center mb-6">
        <input
          type="file"
          accept="image/*"
          onChange={handleUpload}
          className="border p-3 rounded-lg bg-white shadow hover:shadow-lg transition duration-200 cursor-pointer"
        />
      </div>

      {loading && (
        <p className="text-center text-blue-600 font-semibold animate-pulse">
          Extracting data, please wait...
        </p>
      )}

      {error && (
        <p className="text-center text-red-600 font-semibold">{error}</p>
      )}

      <div className="flex flex-col md:flex-row gap-8 mt-8">
        {uploadedImage && (
          <div className="flex-1 flex justify-center">
            <img
              src={uploadedImage}
              alt="Uploaded Passport"
              className="rounded-xl shadow-xl max-h-[500px] border border-gray-300"
            />
          </div>
        )}

        {Object.keys(extractedData).length > 0 && (
          <div className="flex-1">
            <h2 className="text-2xl font-semibold mb-4 text-center md:text-left text-blue-800">
              Extracted Data
            </h2>
            <div className="overflow-x-auto">
              <table className="min-w-full bg-white shadow-lg rounded-xl overflow-hidden">
                <thead className="bg-blue-600 text-white">
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-medium">Field</th>
                    <th className="px-6 py-3 text-left text-sm font-medium">Value</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(extractedData).map(([key, value], index) => (
                    <tr
                      key={index}
                      className={`border-b ${index % 2 === 0 ? "bg-blue-50" : "bg-white"} hover:bg-blue-100`}
                    >
                      <td className="px-6 py-3 capitalize text-gray-700">{key.replace(/_/g, " ")}</td>
                      <td className="px-6 py-3 text-gray-900">{value || "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;


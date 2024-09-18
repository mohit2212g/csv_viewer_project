import React, { useState, useEffect } from "react";
import "./Header.css";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import Loader from "../components/Loader";
import logo from "./logo.svg";

const Header = ({ onFileUpload }) => {
  const navigate = useNavigate();
  const [totalRecords, setTotalRecords] = useState(0);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const username = localStorage.getItem("user");

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    console.log("Selected file:", selectedFile);
    setFile(selectedFile);
  };

  const handleUpload = async () => {
    if (!file) {
      alert("Please select a file first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("username", username);

    setLoading(true);

    try {
      const response = await axios.post(
        `http://192.168.10.107:5001/upload-csv/${username}`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );
      console.log("Response:", response.data);
      alert("File uploaded successfully");
      await fetchTotalRecords();
      if (onFileUpload) onFileUpload();
    } catch (error) {
      console.error("Error uploading file:", error);
      alert("Error uploading file");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    console.log("Logout buttun clicked");

    localStorage.removeItem("token");
    localStorage.removeItem("user");

    navigate("/");
  };

  useEffect(() => {
    fetchTotalRecords();
  }, [username]);

  const fetchTotalRecords = async () => {
    try {
      const response = await axios.get(
        `http://192.168.10.107:5001/total-records/${username}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );
      setTotalRecords(response.data.total_records);
    } catch (error) {
      console.error("Error fetching total records:", error);
    }
  };

  return (
    <header className="header">
      {loading && <Loader />}
      <img src={logo} alt="FINDOC" />
      <nav>
        <ul>
          <li>
            <h2>Total Records : {totalRecords}</h2>
          </li>
          <li>
            <div>
              <input type="file" onChange={handleFileChange} />
              <button onClick={handleUpload}>Upload CSV</button>
            </div>
          </li>
          <li>
            <button onClick={handleLogout}>Logout</button>
          </li>
        </ul>
      </nav>
    </header>
  );
};

export default Header;

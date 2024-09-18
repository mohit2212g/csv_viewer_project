import React, { useEffect, useState } from "react";
import axios from "axios";
import "./FilterData.css";
import Header from "../components/Header";
import Loader from "../components/Loader";
import { useNavigate, useLocation } from "react-router-dom";

const FilterData = () => {
  const [filteredData, setFilteredData] = useState([]);
  const [columns, setColumns] = useState([]);
  const [filters, setFilters] = useState({});
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [totalFilteredRecords, setTotalFilteredRecords] = useState(0);
  const username = localStorage.getItem("user");
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const queryParams = new URLSearchParams(location.search);
    const initialFilters = location.state?.filters || {};
    for (const [key, value] of queryParams.entries()) {
      if (key.startsWith("filter_")) {
        initialFilters[key.replace("filter_", "")] = value;
      } else if (key === "page") {
        setPage(Number(value));
      }
    }
    setFilters(initialFilters);
  }, [location.search]);

  const fetchFilteredData = async () => {
    setLoading(true);
    try {
      const response = await axios.get(
        `http://192.168.10.107:5001/filtered-data/${username}`,
        {
          params: {
            filters: JSON.stringify(filters),
            page,
          },
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );
      const data = response.data.data || [];
      setFilteredData(data);
      if (data.length > 0) {
        const allColumns = Object.keys(data[0]);
        const numericColumns = allColumns
          .filter((col) => col.match(/^col\d+$/))
          .sort(
            (a, b) =>
              parseInt(a.replace("col", "")) - parseInt(b.replace("col", ""))
          );
        const remainingColumns = allColumns.filter(
          (col) => !col.match(/^col\d+$/)
        );
        const sortedColumns = [ ...numericColumns, ...remainingColumns];
        setColumns(sortedColumns);
      }
    } catch (error) {
      console.error("Error fetching filtered data:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTotalFilteredRecords = async () => {
    try {
      const response = await axios.get(
        `http://192.168.10.107:5001/total-filter-records/${username}`,
        {
          params: {
            filters: JSON.stringify(filters),
          },
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );
      setTotalFilteredRecords(response.data.total_records);
    } catch (error) {
      console.error("Error fetching total filtered records:", error);
    }
  };

  useEffect(() => {
    fetchTotalFilteredRecords();
    fetchFilteredData();
  }, [filters, page]);

  const handleFilterChange = (e, columnName) => {
    const { value } = e.target;
    const newFilters = { ...filters, [columnName]: value };
    setFilters(newFilters);
    updateURL(newFilters, page);
  };

  const clearFilters = () => {
    setFilters({});
    updateURL({}, 1);
  };

  const nextPage = () => {
    setPage((prevPage) => {
      const newPage = prevPage + 1;
      updateURL(filters, newPage);
      return newPage;
    });
  };

  const handlePrevPage = () => {
    if (page > 1) {
      setPage((prevPage) => {
        const newPage = prevPage - 1;
        updateURL(filters, newPage);
        return newPage;
      });
    }
  };

  const updateURL = (filters, page) => {
    const queryParams = new URLSearchParams();
    for (const [key, value] of Object.entries(filters)) {
      queryParams.append(`filter_${key}`, value);
    }
    queryParams.append("page", page);
    navigate(`?${queryParams.toString()}`);
  };

  const downloadFilteredFile = async () => {
    setLoading(true);
    try {
      const response = await axios.get(
        `http://192.168.10.107:5001/download-filtered-file/${username}`,
        {
          params: {
            filters: JSON.stringify(filters),
          },
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
          responseType: 'blob', // Important for handling file downloads
        }
      );
      // Create a URL for the file and trigger the download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'filtered_data.csv'); // Name of the downloaded file
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error("Error downloading filtered file:", error);
    } finally {
      setLoading(false);
    }
  }

  const navigateToHome = () => {
    navigate("/DataTable", { state: { filters } });
  };

  return (
    <div>
      <Header />
      {loading && <Loader />}
      <div className="data-table-container">
        <nav className="filter-nav">
          <ul>
            <li>
              <button onClick={navigateToHome}>Back To Home Page</button>
            </li>
            <li>
              <h2>Total Filter Records : {totalFilteredRecords}</h2>
            </li>
          </ul>
        </nav>
        <table>
          <thead>
            <tr>
              <th>#</th>
              {columns.map((key, idx) => (
                <th key={idx}>{key}</th>
              ))}
            </tr>
            <tr>
              <th></th>
              {columns.map((key, idx) => (
                <th key={idx}>
                  <input
                    type="text"
                    placeholder={`Filter ${idx + 1}`}
                    value={filters[key] || ""}
                    onChange={(e) => handleFilterChange(e, key)}
                  />
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filteredData.map((item, index) => (
              <tr key={index}>
                <td>{index + 1}</td>
                {columns.map((key, idx) => (
                  <td key={idx}>{item[key]}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="button-container">
        <ul>
          <li>
            <button onClick={clearFilters}>Clear Filters</button>
          </li>
          <li>
            <button onClick={handlePrevPage}>Previous Page</button>
          </li>
          <li>
            <button onClick={nextPage}>Next Page</button>
          </li>
          <li>
            <button onClick={downloadFilteredFile}>Download Filtered File</button>
          </li>
        </ul>
      </div>
    </div>
  );
};

export default FilterData;

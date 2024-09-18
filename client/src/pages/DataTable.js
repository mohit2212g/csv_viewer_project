import React, { useEffect, useState } from "react";
import axios from "axios";
import "./DataTable.css";
import Header from "../components/Header";
import { useNavigate, useLocation } from "react-router-dom";
import Loader from "../components/Loader";

const DataTable = () => {
  const [tableData, setTableData] = useState([]);
  const [columns, setColumns] = useState([]);
  const [filters, setFilters] = useState({});
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const username = localStorage.getItem("user");
  const navigate = useNavigate();
  const location = useLocation();

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

  const fetchTableData = async () => {
    setLoading(true);
    try {
      const response = await axios.get(
        `http://192.168.10.107:5001/table-data/${username}`,
        {
          params: {
            page,
          },
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );
      const data = response.data.data || [];
      setTableData(data);
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
      console.error("Error fetching table data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTableData();
  }, [username, page]);

  const handleFilterChange = (e, columnName) => {
    const { value } = e.target;
    setFilters((prevFilters) => ({
      ...prevFilters,
      [columnName]: value,
    }));
  };

  const clearFilters = () => {
    setLoading(true);
    setFilters({});
    setLoading(false);
  };

  const filteredData = tableData.filter((item) => {
    return Object.keys(filters).every((key) => {
      if (filters[key] === "") return true; 
      return (
        item[key] &&
        item[key].toString().toLowerCase().includes(filters[key].toLowerCase())
      );
    });
  });

  const nextPage = () => {
    setLoading(true);
    setPage((prevPage) => prevPage + 1);
    setLoading(false);
  };

  const handlePrevPage = () => {
    setLoading(true);
    if (page > 1) {
      setPage((prevPage) => prevPage - 1);
    }
    setLoading(false);
  };

  const handleFilterAllData = () => {
    navigate("/filter-data", { state: { filters } });
  };

  useEffect(() => {
    navigate(".", { state: { filters } });
  }, [filters, navigate]);

  const refreshData = () => {
    fetchTableData();
  };

  return (
    <div>
      <Header onFileUpload={refreshData} />
      {loading && <Loader />}
      <div className="data-table-container">
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
            <button onClick={handleFilterAllData}>Filter All Data</button>
          </li>
        </ul>
      </div>
    </div>
  );
};

export default DataTable;

import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './FilterData.css';
import Header from '../components/Header';
import { useLocation } from 'react-router-dom';
import Loader from '../components/Loader';

const FilterData = () => {
  const [filteredData, setFilteredData] = useState([]);
  const [columns, setColumns] = useState([]);
  const [page, setPage] = useState(1);
  const location = useLocation();
  const { filters, setFilters } = location.state || {};
  const [loading, setLoading] = useState(false);
  const username = localStorage.getItem('user');


  const fetchFilteredData = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`http://localhost:5001/filtered-data/${username}`, {
        params: {
          filters: JSON.stringify(filters),
          page
        },
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = response.data.data || [];
      setFilteredData(data);
      if (data.length > 0) {
        const allColumns = Object.keys(data[0]);
        const numericColumns = allColumns.filter(col => col.match(/^col\d+$/)).sort((a, b) => parseInt(a.replace('col', '')) - parseInt(b.replace('col', '')));
        const remainingColumns = allColumns.filter(col => !col.match(/^col\d+$/) && col !== 'id');
        const sortedColumns = ['id', ...numericColumns, ...remainingColumns];
        setColumns(sortedColumns);
      }
    } catch (error) {
      console.error('Error fetching filtered data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFilteredData();
  }, [filters, page]);

  const nextPage = () => {
    setPage(prevPage => prevPage + 1);
  };

  const handlePrevPage = () => {
    if (page > 1) {
      setPage(prevPage => prevPage - 1);
    }
  };

    // Handle filter change
const handleFilterChange = (e, columnName) => {
  const { value } = e.target;
  setFilters(prevFilters => ({
    ...prevFilters,
    [columnName]: value,
  }));
};

const clearFilters = () => {
  setLoading(true);
  setFilters({});
  setLoading(false);
};

  return (
    <div>
      <Header />
      {loading && <Loader />}
      <div className="data-table-container">
        <h1>Filter Data</h1>
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
                    value={filters[key] || ''}
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
          <li><button onClick={clearFilters}>Clear Filters</button></li>
          <li><button onClick={handlePrevPage}>Previous Page</button></li>
          <li><button onClick={nextPage}>Next Page</button></li>
        </ul>
      </div>
    </div>
  );
};

export default FilterData;

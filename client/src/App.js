import React from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import Login from "./pages/Login";
import DataTable from "./pages/DataTable";
import FilterData from "./pages/FilterData";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/DataTable" element={<DataTable />} /> 
        <Route path="/filter-data" element={<FilterData />} />
      </Routes>
    </Router>

  );
}

export default App;

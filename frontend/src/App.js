import React from "react";
import "@fontsource/roboto/300.css";
import "@fontsource/roboto/400.css";
import "@fontsource/roboto/500.css";
import "@fontsource/roboto/700.css";
import "./App.css";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import CssBaseline from "@mui/material/CssBaseline";
import useMediaQuery from "@mui/material/useMediaQuery";

import Login from "./components/users/Login";
import Home from "./components/home";
import DriveHome from "./components/file-explorer/root";
import Volume from "./components/file-explorer/volume";
import File from "./components/file-explorer/file";
import FileSearchResult from "./components/file-explorer/file/SearchResult";
import MediaPlayer from "./components/media-player";
import Playlist from "./components/media-player/Playlist";
import Settings from "./components/settings";
import Network from "./components/settings/network";
import System from "./components/settings/system";
import Users from "./components/settings/users";
import Profile from "./components/profile";
import ErrorPage from "./utils/ErrorPage";
import { red, amber, pink, grey } from "@mui/material/colors";

function App() {
  const prefersDarkMode = useMediaQuery("(prefers-color-scheme: dark)");
  const fixedMode = localStorage.getItem("theme") || "system";
  const theme = React.useMemo(
    () =>
      createTheme({
        palette: {
          mode: fixedMode === "dark" || prefersDarkMode ? "dark" : "light",
          ...(fixedMode === "dark" || prefersDarkMode
            ? {
                primary: {
                  main: pink[700],
                },
                background: {
                  default: grey[900],
                  paper: grey[800],
                },
                secondary: {
                  main: red[800],
                },
              }
            : {
                primary: {
                  main: amber[500],
                },
                secondary: {
                  main: red[500],
                },
              }),
        },
      }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [prefersDarkMode]
  );

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <Routes>
          <Route path="*" element={<ErrorPage />} />
          <Route path="/drive" element={<Home />} />
          <Route path="/drive/login" element={<Login />} />
          <Route path="/drive/my-drive" element={<DriveHome />}>
            <Route path="" element={<Volume />} />
          </Route>
          <Route path="/drive/folder" element={<DriveHome />}>
            <Route path="search" element={<FileSearchResult />} />
            <Route path=":fileId" element={<File />} />
          </Route>
          <Route path="/drive/media-player" element={<MediaPlayer />}>
            <Route path=":playlistId" element={<Playlist />} />
          </Route>
          <Route path="/drive/settings" element={<Settings />}>
            <Route path="users" element={<Users />} />
            <Route path="network" element={<Network />} />
            <Route path="system" element={<System />} />
          </Route>
          <Route path="/drive/profile" element={<Profile />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;

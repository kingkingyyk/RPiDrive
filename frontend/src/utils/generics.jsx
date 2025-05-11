import axios from "axios";

export const ajax = axios.create({
  withCredentials: true,
  xsrfHeaderName: "X-CSRFToken",
  xsrfCookieName: "csrftoken",
});

export const formatUsername = (user) => {
  if (!user) return "";

  let result = "";
  if (user.first_name) {
    result += user.first_name;
  }
  if (user.last_name) {
    if (result.length > 0) result += " ";
    result += user.last_name;
  }
  if (!result) {
    result = user.username;
  }
  return result;
};

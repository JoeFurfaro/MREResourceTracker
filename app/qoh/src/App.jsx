import './App.scss';
import 'bootstrap/dist/css/bootstrap.min.css';
import {Container} from "react-bootstrap";
import React, {useState, useEffect} from "react";
import {testData} from "./data";
import mreLogo from "./mre.png";
import axios from "axios";
import warningImg from "./warning.png";
import fe_light from "./fe_light.png";

const TextPair = ({top, bottom}) => {
  return (
    <>
      <p className="mt-0 mb-0">
        {top}
      </p>
      <p className="mt-0 mb-0">
        <b>
          {bottom}
        </b>
      </p>
    </>
  );
}

const Loading = () => {

  const [dots, setDots] = useState("");

  useEffect(() => {
    let interval = setInterval(() => {
      setDots((curDots) => curDots.length === 5 ? "." : curDots + ".");
    }, 350);

    return () => clearInterval(interval);
  }, []);

  return (
    <h1 className="loading-text">Loading recent data{dots}</h1>
  );
}

export const App = () => {

  document.title = "Martinrea Resource Tracker";

  const [parts, setParts] = useState([]);
  const [err, setErr] = useState(false);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState(null);

  let args = window.location.href.split("/");
  let resource = args.length === 0 || args[0] === "" ? null : args[args.length - 1];

  useEffect(() => {
    refresh();

    let interval = setInterval(() => {
      refresh();
    }, 60*3000);

    let refreshInterval = setInterval(() => {
      window.location.reload();
    }, 1000*60*60);

    return () => {
      clearInterval(interval);
      clearInterval(refreshInterval);
    }
  }, []);


  if(resource === null || resource === "") { 
    return <h1>Please specify a resource!</h1>
  }
  const refresh = () => {
    let dev = false;
    let url = dev ? "http://10.99.0.146:9009/" : "/"; 
    axios.get(url + "tracker/" + resource).then((res) => {
        setParts(res.data);
        setLoading(false);
        setErr(false);
        setLastRefresh(new Date());
    }).catch((err) => {
        setErr(true);
        setLoading(false);
    });
  }

  return (
    <div className="App">
        <div className="cell-label">
          <img className="cell-label-image" src={mreLogo} />
          <h1 className="cell-label-text">Resource: <b>{resource}</b></h1>
        </div>

        <div className="powered-by">
          <img src={fe_light} className="powered-by-logo" />
          <p className="powered-by-text d-inline">
            Powered by FactoryEngine
          </p>
        </div>


        <Container fluid>
          {!err ? 
          (
            <>
              {lastRefresh == null ? null : (
                <div className="time-update">
                  <p className="mb-0 error-text"><b>Last refresh: </b> {lastRefresh.toLocaleString()}</p>
                </div>
              )}
            </>
          ) : (
            <div className="error">
              <p className="mb-0 error-text"><img src={warningImg} className="warning-icon" /><b>Warning: Unable to refresh data. This data may not reflect recent changes.</b> {lastRefresh === null ? null : "Last successful refresh: " + lastRefresh.toLocaleString()}</p>
            </div>
          )}
          <div className="row mt-5">
            <div className="col-10 mx-auto">
                  {parts.length === 0 ? null : (
                    <table className="w-100">
                      <thead>
                        <tr className="table-row">
                          <th className="table-heading part-no-heading"><b>Part #</b></th>
                          <th className="table-heading qoh-heading"><b>Current QOH</b></th>
                          <th className="invis-heading"></th>
                          {parts[0].Quants.slice(0, 7).map((q) => {
                            let d = new Date(q.Date);
                            const dayNames = ["Mon", "Tues", "Wed", "Thurs", "Fri", "Sat", "Sun"];
                            const months = ["Jan", "Feb", "Mar", "Apr", "May", "June", "July", "Aug", "Sep", "Oct", "Nov", "Dec"];
                            const weekDay = dayNames[d.getDay()];
                            const month = months[d.getMonth()];
                            const dayOfMonth = d.getUTCDate();

                              return (
                                      <th className="qoh-heading table-heading"><b>{weekDay}</b>&nbsp;{month}&nbsp;{dayOfMonth}</th>
                              );
                          })}
                        </tr>
                      </thead>
                      <tbody>
                      {parts.map((part) => {
                        let quants = part.Quants.slice(0, 7);

                        return (
                          <tr className="table-row">
                              <td className="pt-4 pb-4 part-no">
                                  <b>{part.PartNo}</b>
                              </td>
                              <td className="pt-4 pb-4 cur-qoh qoh-cell">
                                  <b>{part.QOH}</b>
                              </td>
                              <td className="invis-cell ic-bordered"></td>
                              {quants.map((q) => {
                                  return (
                                        <td className={"projected-qoh qoh-cell pt-4 pb-4 " + (q.MinQOH === null ? "no-change" : (q.MinQOH > 0 ? "good" : "bad"))}>
                                          <b>{q.MinQOH === null ? "" : q.MinQOH}</b>
                                        </td>
                                  );
                              })}
                          </tr>
                        );
                        })}
                      </tbody>
                    </table>
                  )}
            </div>
            {
              !loading ? null : (
                <div className="row mt-5">
                    <div className="col-12 text-center">
                      <Loading />
                    </div>
                </div>
              )
            }
          </div>
        </Container>
    </div>
  );
}
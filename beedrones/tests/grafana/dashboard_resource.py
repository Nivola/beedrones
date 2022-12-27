# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2020-2022 Regione Piemonte

dash_resource='''{
  "dashboard": {
    "annotations": {
      "list": [
      {
        "builtIn": 1,
        "datasource": "-- Grafana --",
        "enable": true,
        "hide": true,
        "iconColor": "rgba(0, 211, 255, 1)",
        "limit": 100,
        "name": "Annotations & Alerts",
        "showIn": 0,
        "type": "dashboard"
      }
    ]
  },
  "editable": true,
  "gnetId": null,
  "graphTooltip": 0,
  "links": [],
  "panels": [
    {
      "cacheTimeout": null,
      "colorBackground": false,
      "colorPostfix": false,
      "colorPrefix": false,
      "colorValue": true,
      "colors": [
        "#629e51",
        "rgba(237, 129, 40, 0.89)",
        "rgba(245, 54, 54, 0.9)"
      ],
      "datasource": "$datasource",
      "decimals": null,
      "editable": true,
      "error": false,
      "format": "none",
      "gauge": {
        "maxValue": 100,
        "minValue": 0,
        "show": false,
        "thresholdLabels": false,
        "thresholdMarkers": true
      },
      "gridPos": {
        "h": 3,
        "w": 10,
        "x": 0,
        "y": 0
      },
      "id": 3,
      "interval": null,
      "isNew": true,
      "links": [],
      "mappingType": 1,
      "mappingTypes": [
        {
          "name": "value to text",
          "value": 1
        },
        {
          "name": "range to text",
          "value": 2
        }
      ],
      "maxDataPoints": 100,
      "nullPointMode": "connected",
      "nullText": null,
      "postfix": "",
      "postfixFontSize": "50%",
      "prefix": "",
      "prefixFontSize": "50%",
      "rangeMaps": [
        {
          "from": "null",
          "text": "N/A",
          "to": "null"
        }
      ],
      "sparkline": {
        "fillColor": "rgba(31, 118, 189, 0.18)",
        "full": false,
        "lineColor": "rgb(31, 120, 193)",
        "show": true
      },
      "tableColumn": "",
      "targets": [
        {
          "application": {
            "filter": "General"
          },
          "functions": [],
          "group": {
            "filter": "$gruppo"
          },
          "host": {
            "filter": "$VMdiscovered"
          },
          "item": {
            "filter": "Host name"
          },
          "mode": 2,
          "options": {
            "showDisabledItems": false,
            "skipEmptyValues": false
          },
          "refId": "A",
          "resultFormat": "Table",
          "table": {
            "skipEmptyValues": false
          },
          "triggers": {
            "acknowledged": 2,
            "count": true,
            "minSeverity": 3
          }
        }
      ],
      "thresholds": "",
      "title": "Host name",
      "type": "singlestat",
      "valueFontSize": "70%",
      "valueMaps": [
        {
          "op": "=",
          "text": "N/A",
          "value": "null"
        }
      ],
      "valueName": "avg"
    },
    {
      "cacheTimeout": null,
      "colorBackground": false,
      "colorValue": false,
      "colors": [
        "#299c46",
        "rgba(237, 129, 40, 0.89)",
        "#d44a3a"
      ],
      "format": "none",
      "gauge": {
        "maxValue": 100,
        "minValue": 0,
        "show": false,
        "thresholdLabels": false,
        "thresholdMarkers": true
      },
      "gridPos": {
        "h": 3,
        "w": 4,
        "x": 10,
        "y": 0
      },
      "id": 19,
      "interval": null,
      "links": [],
      "mappingType": 1,
      "mappingTypes": [
        {
          "name": "value to text",
          "value": 1
        },
        {
          "name": "range to text",
          "value": 2
        }
      ],
      "maxDataPoints": 100,
      "nullPointMode": "connected",
      "nullText": null,
      "datasource": "$datasource",
      "postfix": "",
      "postfixFontSize": "50%",
      "prefix": "",
      "prefixFontSize": "50%",
      "rangeMaps": [
        {
          "from": "null",
          "text": "N/A",
          "to": "null"
        }
      ],
      "sparkline": {
        "fillColor": "rgba(31, 118, 189, 0.18)",
        "full": false,
        "lineColor": "rgb(31, 120, 193)",
        "show": false
      },
      "tableColumn": "",
      "targets": [
        {
          "application": {
            "filter": "OS"
          },
          "functions": [],
          "group": {
            "filter": "$gruppo"
          },
          "host": {
            "filter": "$VMdiscovered"
          },
          "item": {
            "filter": "Number of logged in users"
          },
          "mode": 0,
          "options": {
            "showDisabledItems": false,
            "skipEmptyValues": false
          },
          "refId": "A",
          "resultFormat": "time_series",
          "table": {
            "skipEmptyValues": false
          },
          "triggers": {
            "acknowledged": 2,
            "count": true,
            "minSeverity": 3
          }
        }
      ],
      "thresholds": "",
      "title": "Logged in user",
      "type": "singlestat",
      "valueFontSize": "80%",
      "valueMaps": [
        {
          "op": "=",
          "text": "N/A",
          "value": "null"
        }
      ],
      "valueName": "current"
    },
    {
      "cacheTimeout": null,
      "colorBackground": false,
      "colorValue": true,
      "colors": [
        "rgba(245, 54, 54, 0.9)",
        "rgba(237, 129, 40, 0.89)",
        "rgba(50, 172, 45, 0.97)"
      ],
      "datasource": "$datasource",
      "decimals": 0,
      "editable": true,
      "error": false,
      "datasource": "$datasource",
      "format": "s",
      "gauge": {
        "maxValue": 100,
        "minValue": 0,
        "show": false,
        "thresholdLabels": false,
        "thresholdMarkers": true
      },
      "gridPos": {
        "h": 3,
        "w": 3,
        "x": 14,
        "y": 0
      },
      "id": 4,
      "interval": null,
      "isNew": true,
      "links": [],
      "mappingType": 1,
      "mappingTypes": [
        {
          "name": "value to text",
          "value": 1
        },
        {
          "name": "range to text",
          "value": 2
        }
      ],
      "maxDataPoints": "",
      "nullPointMode": "connected",
      "nullText": null,
      "postfix": "",
      "postfixFontSize": "50%",
      "prefix": "",
      "prefixFontSize": "50%",
      "rangeMaps": [
        {
          "from": "null",
          "text": "N/A",
          "to": "null"
        }
      ],
      "sparkline": {
        "fillColor": "rgba(31, 118, 189, 0.18)",
        "full": false,
        "lineColor": "rgb(31, 120, 193)",
        "show": false
      },
      "tableColumn": "",
      "targets": [
        {
          "application": {
            "filter": "General"
          },
          "functions": [],
          "group": {
            "filter": "$gruppo"
          },
          "hide": false,
          "host": {
            "filter": "$VMdiscovered"
          },
          "item": {
            "filter": "System uptime"
          },
          "mode": 0,
          "options": {
            "showDisabledItems": false,
            "skipEmptyValues": false
          },
          "refId": "A",
          "resultFormat": "time_series",
          "table": {
            "skipEmptyValues": false
          },
          "triggers": {
            "acknowledged": 2,
            "count": true,
            "minSeverity": 3
          }
        }
      ],
      "thresholds": "",
      "title": "Uptime",
      "type": "singlestat",
      "valueFontSize": "70%",
      "valueMaps": [
        {
          "op": "=",
          "text": "N/A",
          "value": "null"
        }
      ],
      "valueName": "current"
    },
    {
      "cacheTimeout": null,
      "colorBackground": false,
      "colorValue": false,
      "colors": [
        "#299c46",
        "rgba(237, 129, 40, 0.89)",
        "#d44a3a"
      ],
      "format": "none",
      "gauge": {
        "maxValue": 100,
        "minValue": 0,
        "show": false,
        "thresholdLabels": false,
        "thresholdMarkers": true
      },
      "gridPos": {
        "h": 3,
        "w": 7,
        "x": 17,
        "y": 0
      },
      "id": 9,
      "interval": null,
      "links": [],
      "mappingType": 1,
      "mappingTypes": [
        {
          "name": "value to text",
          "value": 1
        },
        {
          "name": "range to text",
          "value": 2
        }
      ],
      "maxDataPoints": 100,
      "nullPointMode": "connected",
      "datasource": "$datasource",
      "nullText": null,
      "postfix": "",
      "postfixFontSize": "50%",
      "prefix": "",
      "prefixFontSize": "50%",
      "rangeMaps": [
        {
          "from": "null",
          "text": "N/A",
          "to": "null"
        }
      ],
      "sparkline": {
        "fillColor": "rgba(31, 118, 189, 0.18)",
        "full": true,
        "lineColor": "rgb(31, 120, 193)",
        "show": true
      },
      "tableColumn": "",
      "targets": [
        {
          "application": {
            "filter": "General"
          },
          "functions": [],
          "group": {
            "filter": "$gruppo"
          },
          "hide": false,
          "host": {
            "filter": "$VMdiscovered"
          },
          "item": {
            "filter": "System information"
          },
          "mode": 2,
          "options": {
            "showDisabledItems": false,
            "skipEmptyValues": false
          },
          "refId": "A",
          "resultFormat": "time_series",
          "slaProperty": {
            "name": "SLA",
            "property": "sla"
          },
          "table": {
            "skipEmptyValues": false
          },
          "triggers": {
            "acknowledged": 2,
            "count": true,
            "minSeverity": 3
          }
        }
      ],
      "thresholds": "",
      "title": "System information",
      "type": "singlestat",
      "valueFontSize": "30%",
      "valueMaps": [
        {
          "op": "=",
          "text": "N/A",
          "value": "null"
        }
      ],
      "valueName": "avg"
    },
    {
      "ackEventColor": "rgb(56, 219, 156)",
      "ageField": false,
      "customLastChangeFormat": false,
      "datasources": [
        "$datasource"
      ],
      "descriptionAtNewLine": false,
      "descriptionField": true,
      "fontSize": "100%",
      "gridPos": {
        "h": 8,
        "w": 14,
        "x": 0,
        "y": 3
      },
      "highlightBackground": true,
      "highlightNewEvents": true,
      "highlightNewerThan": "1h",
      "hostField": true,
      "hostGroups": false,
      "hostProxy": false,
      "hostTechNameField": false,
      "hostsInMaintenance": true,
      "id": 11,
      "lastChangeFormat": "",
      "layout": "table",
      "limit": 100,
      "links": [],
      "markAckEvents": true,
      "okEventColor": "rgb(56, 189, 113)",
      "pageSize": 5,
      "problemTimeline": true,
      "resizedColumns": [],
      "schemaVersion": 6,
      "severityField": true,
      "showEvents": {
        "text": "All",
        "value": [
          0,
          1
        ]
      },
      "showTags": false,
      "showTriggers": "all triggers",
      "sortTriggersBy": {
        "text": "last change",
        "value": "lastchange"
      },
      "statusField": true,
      "statusIcon": false,
      "targets": {
        "0": {
          "application": {
            "filter": ""
          },
          "group": {
            "filter": ""
          },
          "host": {
            "filter": ""
          },
          "proxy": {
            "filter": ""
          },
          "tags": {
            "filter": ""
          },
          "trigger": {
            "filter": ""
          }
        },
        "$datasource": {
          "application": {
            "filter": "/.*/"
          },
          "group": {
            "filter": "$gruppo"
          },
          "host": {
            "filter": "$VMdiscovered"
          },
          "proxy": {
            "filter": ""
          },
          "tags": {
            "filter": ""
          },
          "trigger": {
            "filter": "/.*/"
          }
        },
        "null": {
          "application": {
            "filter": ""
          },
          "group": {
            "filter": "$gruppo"
          },
          "host": {
            "filter": "$VMdiscovered"
          },
          "proxy": {
            "filter": ""
          },
          "tags": {
            "filter": ""
          },
          "trigger": {
            "filter": null
          }
        }
      },
      "title": "Alert and Notification",
      "triggerSeverity": [
        {
          "color": "rgb(108, 108, 108)",
          "priority": 0,
          "severity": "Not classified",
          "show": true
        },
        {
          "color": "rgb(120, 158, 183)",
          "priority": 1,
          "severity": "Information",
          "show": true
        },
        {
          "color": "rgb(175, 180, 36)",
          "priority": 2,
          "severity": "Warning",
          "show": true
        },
        {
          "color": "rgb(255, 137, 30)",
          "priority": 3,
          "severity": "Average",
          "show": true
        },
        {
          "color": "rgb(255, 101, 72)",
          "priority": 4,
          "severity": "High",
          "show": true
        },
        {
          "color": "rgb(215, 0, 0)",
          "priority": 5,
          "severity": "Disaster",
          "show": true
        }
      ],
      "type": "alexanderzobnin-zabbix-triggers-panel"
    },
    {
      "aliasColors": {},
      "bars": false,
      "dashLength": 10,
      "dashes": false,
      "datasource": "$datasource",
      "editable": true,
      "error": false,
      "fill": 0,
      "grid": {},
      "gridPos": {
        "h": 8,
        "w": 10,
        "x": 14,
        "y": 3
      },
      "id": 7,
      "isNew": true,
      "legend": {
        "avg": false,
        "current": false,
        "max": false,
        "min": false,
        "show": true,
        "total": false,
        "values": false
      },
      "lines": true,
      "linewidth": 2,
      "links": [],
      "nullPointMode": "connected",
      "percentage": false,
      "pointradius": 5,
      "points": false,
      "renderer": "flot",
      "seriesOverrides": [],
      "spaceLength": 10,
      "stack": false,
      "steppedLine": false,
      "targets": [
        {
          "application": {
            "filter": "Processes"
          },
          "functions": [],
          "group": {
            "filter": "$gruppo"
          },
          "host": {
            "filter": "$VMdiscovered"
          },
          "item": {
            "filter": "/.*/"
          },
          "mode": 0,
          "options": {
            "showDisabledItems": false,
            "skipEmptyValues": false
          },
          "refId": "A",
          "resultFormat": "time_series",
          "table": {
            "skipEmptyValues": false
          },
          "triggers": {
            "acknowledged": 2,
            "count": true,
            "minSeverity": 3
          }
        },
        {
          "application": {
            "filter": "Zabbix server"
          },
          "functions": [],
          "group": {
            "filter": "Zabbix servers"
          },
          "host": {
            "filter": "Zabbix server"
          },
          "item": {
            "filter": "/Values processed/"
          },
          "mode": 0,
          "options": {
            "showDisabledItems": false,
            "skipEmptyValues": false
          },
          "refId": "B",
          "resultFormat": "time_series",
          "table": {
            "skipEmptyValues": false
          },
          "triggers": {
            "acknowledged": 2,
            "count": true,
            "minSeverity": 3
          }
        }
      ],
      "thresholds": [
        {
          "colorMode": "custom",
          "fill": false,
          "line": true,
          "lineColor": "rgb(255, 0, 0)",
          "op": "gt",
          "source": "zabbix",
          "value": 30
        },
        {
          "colorMode": "custom",
          "fill": false,
          "line": true,
          "lineColor": "rgb(255, 0, 0)",
          "op": "gt",
          "source": "zabbix",
          "value": 300
        }
      ],
      "timeFrom": null,
      "timeRegions": [],
      "timeShift": null,
      "title": "Processes",
      "tooltip": {
        "msResolution": false,
        "shared": true,
        "sort": 0,
        "value_type": "cumulative"
      },
      "type": "graph",
      "xaxis": {
        "buckets": null,
        "mode": "time",
        "name": null,
        "show": true,
        "values": []
      },
      "yaxes": [
        {
          "format": "short",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": null,
          "show": true
        },
        {
          "format": "short",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": null,
          "show": true
        }
      ],
      "yaxis": {
        "align": false,
        "alignLevel": null
      }
    },
    {
      "aliasColors": {},
      "bars": false,
      "dashLength": 10,
      "dashes": false,
      "datasource": "$datasource",
      "editable": true,
      "error": false,
      "fill": 0,
      "grid": {},
      "gridPos": {
        "h": 8,
        "w": 14,
        "x": 0,
        "y": 11
      },
      "id": 6,
      "isNew": true,
      "legend": {
        "alignAsTable": true,
        "avg": false,
        "current": false,
        "hideEmpty": true,
        "hideZero": true,
        "max": false,
        "min": false,
        "rightSide": true,
        "show": true,
        "total": false,
        "values": false
      },
      "lines": true,
      "linewidth": 2,
      "links": [],
      "nullPointMode": "connected",
      "percentage": false,
      "pointradius": 5,
      "points": false,
      "renderer": "flot",
      "seriesOverrides": [],
      "spaceLength": 10,
      "stack": false,
      "steppedLine": false,
      "targets": [
        {
          "application": {
            "filter": "Filesystems"
          },
          "functions": [],
          "group": {
            "filter": "$gruppo"
          },
          "hide": false,
          "host": {
            "filter": "$VMdiscovered"
          },
          "item": {
            "filter": "/Free (?!inode).*perc/"
          },
          "mode": 0,
          "options": {
            "showDisabledItems": true,
            "skipEmptyValues": false
          },
          "refId": "A",
          "resultFormat": "time_series",
          "table": {
            "skipEmptyValues": false
          },
          "triggers": {
            "acknowledged": 2,
            "count": true,
            "minSeverity": 3
          }
        }
      ],
      "thresholds": [
        {
          "colorMode": "custom",
          "fill": false,
          "line": true,
          "lineColor": "rgb(255, 0, 0)",
          "op": "gt",
          "source": "zabbix",
          "value": 20
        }
      ],
      "timeFrom": null,
      "timeRegions": [],
      "timeShift": null,
      "title": "Filesystem free (percentage)",
      "tooltip": {
        "msResolution": false,
        "shared": true,
        "sort": 0,
        "value_type": "cumulative"
      },
      "type": "graph",
      "xaxis": {
        "buckets": null,
        "mode": "time",
        "name": null,
        "show": true,
        "values": []
      },
      "yaxes": [
        {
          "decimals": null,
          "format": "percent",
          "label": null,
          "logBase": 1,
          "max": "100",
          "min": "0",
          "show": true
        },
        {
          "format": "short",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": null,
          "show": true
        }
      ],
      "yaxis": {
        "align": false,
        "alignLevel": null
      }
    },
    {
      "columns": [
        {
          "text": "Current",
          "value": "current"
        }
      ],
      "fontSize": "100%",
      "gridPos": {
        "h": 8,
        "w": 10,
        "x": 14,
        "y": 11
      },
      "id": 13,
      "links": [],
      "pageSize": null,
      "datasource": "$datasource",
      "scroll": true,
      "showHeader": true,
      "sort": {
        "col": 0,
        "desc": true
      },
      "styles": [
        {
          "alias": "Valore Corrente",
          "colorMode": null,
          "colors": [
            "rgba(245, 54, 54, 0.9)",
            "rgba(237, 129, 40, 0.89)",
            "rgba(50, 172, 45, 0.97)"
          ],
          "decimals": 2,
          "pattern": "Current",
          "thresholds": [],
          "type": "number",
          "unit": "decbytes"
        }
      ],
      "targets": [
        {
          "application": {
            "filter": "Filesystems"
          },
          "functions": [],
          "group": {
            "filter": "$gruppo"
          },
          "hide": false,
          "host": {
            "filter": "$VMdiscovered"
          },
          "item": {
            "filter": "/Free disk space (?!.*perc.*)/"
          },
          "mode": 0,
          "options": {
            "showDisabledItems": false,
            "skipEmptyValues": false
          },
          "refId": "A",
          "resultFormat": "time_series",
          "table": {
            "skipEmptyValues": false
          },
          "triggers": {
            "acknowledged": 2,
            "count": true,
            "minSeverity": 3
          }
        }
      ],
      "title": "File System Metric",
      "transform": "timeseries_aggregations",
      "type": "table"
    },
    {
      "aliasColors": {},
      "bars": false,
      "dashLength": 10,
      "dashes": false,
      "fill": 1,
      "gridPos": {
        "h": 8,
        "w": 14,
        "x": 0,
        "y": 19
      },
      "id": 15,
      "legend": {
        "alignAsTable": false,
        "avg": true,
        "current": false,
        "max": true,
        "min": true,
        "show": true,
        "total": false,
        "values": true
      },
      "lines": true,
      "linewidth": 1,
      "links": [],
      "nullPointMode": "null",
      "percentage": false,
      "pointradius": 5,
      "points": false,
      "renderer": "flot",
      "seriesOverrides": [],
      "spaceLength": 10,
      "stack": false,
      "steppedLine": false,
      "targets": [
        {
          "application": {
            "filter": "Memory"
          },
          "functions": [],
          "group": {
            "filter": "$gruppo"
          },
          "hide": false,
          "host": {
            "filter": "$VMdiscovered"
          },
          "item": {
            "filter": "/(?:Total memory|Available memory)/"
          },
          "mode": 0,
          "options": {
            "showDisabledItems": false,
            "skipEmptyValues": false
          },
          "refId": "A",
          "resultFormat": "time_series",
          "table": {
            "skipEmptyValues": false
          },
          "triggers": {
            "acknowledged": 2,
            "count": true,
            "minSeverity": 3
          }
        }
      ],
      "thresholds": [
        {
          "colorMode": "custom",
          "fill": false,
          "line": true,
          "lineColor": "rgb(255, 0, 0)",
          "op": "gt",
          "source": "zabbix",
          "value": 20
        }
      ],
      "timeFrom": null,
      "timeRegions": [],
      "timeShift": null,
      "title": "Memory",
      "tooltip": {
        "shared": true,
        "sort": 0,
        "value_type": "individual"
      },
      "type": "graph",
      "xaxis": {
        "buckets": null,
        "mode": "time",
        "name": null,
        "show": true,
        "values": []
      },
      "yaxes": [
        {
          "decimals": null,
          "format": "decbytes",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": "0",
          "show": true
        },
        {
          "format": "short",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": null,
          "show": true
        }
      ],
      "yaxis": {
        "align": false,
        "alignLevel": null
      }
    },
    {
      "columns": [
        {
          "text": "Current",
          "value": "current"
        },
        {
          "text": "Avg",
          "value": "avg"
        }
      ],
      "datasource": "$datasource",
      "editable": true,
      "error": false,
      "fontSize": "100%",
      "gridPos": {
        "h": 8,
        "w": 10,
        "x": 14,
        "y": 19
      },
      "id": 2,
      "isNew": true,
      "links": [],
      "pageSize": null,
      "scroll": true,
      "showHeader": true,
      "sort": {
        "col": 1,
        "desc": true
      },
      "styles": [
        {
          "alias": "",
          "dateFormat": "YYYY-MM-DD HH:mm:ss",
          "decimals": 1,
          "pattern": "Current",
          "type": "number",
          "unit": "decbytes"
        },
        {
          "alias": "",
          "colorMode": null,
          "colors": [
            "rgba(245, 54, 54, 0.9)",
            "rgba(237, 129, 40, 0.89)",
            "rgba(50, 172, 45, 0.97)"
          ],
          "dateFormat": "YYYY-MM-DD HH:mm:ss",
          "decimals": 1,
          "mappingType": 1,
          "pattern": "Avg",
          "thresholds": [],
          "type": "number",
          "unit": "decbytes"
        },
        {
          "colorMode": "cell",
          "colors": [
            "rgb(41, 170, 106)",
            "rgba(239, 148, 21, 0.89)",
            "rgba(239, 10, 10, 0.9)"
          ],
          "decimals": 1,
          "pattern": "/.*/",
          "thresholds": [
            "50",
            "80"
          ],
          "type": "number",
          "unit": "percent"
        }
      ],
      "targets": [
        {
          "application": {
            "filter": "Memory"
          },
          "functions": [],
          "group": {
            "filter": "$gruppo"
          },
          "hide": false,
          "host": {
            "filter": "$VMdiscovered"
          },
          "item": {
            "filter": "/(?:Total memory|Available memory|Total swap space)/"
          },
          "mode": 0,
          "options": {
            "showDisabledItems": false,
            "skipEmptyValues": false
          },
          "refId": "A",
          "resultFormat": "time_series",
          "table": {
            "skipEmptyValues": false
          },
          "triggers": {
            "acknowledged": 2,
            "count": true,
            "minSeverity": 3
          }
        }
      ],
      "title": "Metriche utilizzo memoria",
      "transform": "timeseries_aggregations",
      "type": "table"
    },
    {
      "aliasColors": {},
      "bars": false,
      "dashLength": 10,
      "dashes": false,
      "datasource": "$datasource",
      "editable": true,
      "error": false,
      "fill": 1,
      "grid": {},
      "gridPos": {
        "h": 9,
        "w": 14,
        "x": 0,
        "y": 27
      },
      "id": 1,
      "isNew": true,
      "legend": {
        "alignAsTable": true,
        "avg": false,
        "current": false,
        "max": false,
        "min": false,
        "rightSide": true,
        "show": true,
        "total": false,
        "values": false
      },
      "lines": true,
      "linewidth": 2,
      "links": [],
      "nullPointMode": "connected",
      "percentage": false,
      "pointradius": 5,
      "points": false,
      "renderer": "flot",
      "seriesOverrides": [
        {
          "alias": "/user/",
          "color": "#1F78C1"
        },
        {
          "alias": "/system/",
          "color": "#BF1B00"
        },
        {
          "alias": "/iowait/",
          "color": "#E5AC0E"
        }
      ],
      "spaceLength": 10,
      "stack": true,
      "steppedLine": false,
      "targets": [
        {
          "application": {
            "filter": ""
          },
          "functions": [],
          "group": {
            "filter": "$gruppo"
          },
          "host": {
            "filter": "$VMdiscovered"
          },
          "item": {
            "filter": "/CPU (?!idle)/"
          },
          "mode": 0,
          "options": {
            "showDisabledItems": false,
            "skipEmptyValues": false
          },
          "refId": "A",
          "resultFormat": "time_series",
          "table": {
            "skipEmptyValues": false
          },
          "triggers": {
            "acknowledged": 2,
            "count": true,
            "minSeverity": 3
          }
        }
      ],
      "thresholds": [
        {
          "colorMode": "custom",
          "fill": false,
          "line": true,
          "lineColor": "rgb(255, 0, 0)",
          "op": "gt",
          "source": "zabbix",
          "value": 20
        }
      ],
      "timeFrom": null,
      "timeRegions": [],
      "timeShift": null,
      "title": "CPU",
      "tooltip": {
        "msResolution": false,
        "shared": true,
        "sort": 0,
        "value_type": "individual"
      },
      "type": "graph",
      "xaxis": {
        "buckets": null,
        "mode": "time",
        "name": null,
        "show": true,
        "values": []
      },
      "yaxes": [
        {
          "format": "percent",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": null,
          "show": true
        },
        {
          "format": "short",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": null,
          "show": true
        }
      ],
      "yaxis": {
        "align": false,
        "alignLevel": null
      }
    },
    {
      "aliasColors": {},
      "bars": false,
      "dashLength": 10,
      "dashes": false,
      "fill": 1,
      "gridPos": {
        "h": 9,
        "w": 10,
        "x": 14,
        "y": 27
      },
      "id": 21,
      "legend": {
        "avg": false,
        "current": false,
        "max": false,
        "min": false,
        "show": true,
        "total": false,
        "values": false
      },
      "lines": true,
      "linewidth": 1,
      "links": [],
      "nullPointMode": "null",
      "percentage": false,
      "pointradius": 5,
      "points": false,
      "renderer": "flot",
      "seriesOverrides": [],
      "spaceLength": 10,
      "stack": false,
      "steppedLine": false,
      "targets": [
        {
          "application": {
            "filter": "CPU"
          },
          "functions": [],
          "group": {
            "filter": "$gruppo"
          },
          "host": {
            "filter": "$VMdiscovered"
          },
          "item": {
            "filter": "Processor load (15 min average per core)"
          },
          "mode": 0,
          "options": {
            "showDisabledItems": false,
            "skipEmptyValues": false
          },
          "refId": "A",
          "resultFormat": "time_series",
          "table": {
            "skipEmptyValues": false
          },
          "triggers": {
            "acknowledged": 2,
            "count": true,
            "minSeverity": 3
          }
        }
      ],
      "thresholds": [],
      "timeFrom": null,
      "timeRegions": [],
      "timeShift": null,
      "title": "Processor load (15 min average per core)",
      "tooltip": {
        "shared": true,
        "sort": 0,
        "value_type": "individual"
      },
      "type": "graph",
      "xaxis": {
        "buckets": null,
        "mode": "time",
        "name": null,
        "show": true,
        "values": []
      },
      "yaxes": [
        {
          "format": "short",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": null,
          "show": true
        },
        {
          "format": "short",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": null,
          "show": true
        }
      ],
      "yaxis": {
        "align": false,
        "alignLevel": null
      }
    },
    {
      "aliasColors": {},
      "bars": false,
      "dashLength": 10,
      "dashes": false,
      "fill": 1,
      "gridPos": {
        "h": 7,
        "w": 14,
        "x": 0,
        "y": 36
      },
      "id": 17,
      "legend": {
        "avg": false,
        "current": false,
        "max": false,
        "min": false,
        "show": true,
        "total": false,
        "values": false
      },
      "lines": true,
      "linewidth": 1,
      "links": [],
      "nullPointMode": "null",
      "percentage": false,
      "pointradius": 5,
      "points": false,
      "renderer": "flot",
      "seriesOverrides": [],
      "spaceLength": 10,
      "stack": false,
      "steppedLine": false,
      "targets": [
        {
          "application": {
            "filter": "Network interfaces"
          },
          "functions": [],
          "group": {
            "filter": "$gruppo"
          },
          "host": {
            "filter": "$VMdiscovered"
          },
          "item": {
            "filter": "/.*/"
          },
          "mode": 0,
          "options": {
            "showDisabledItems": false,
            "skipEmptyValues": false
          },
          "refId": "A",
          "resultFormat": "time_series",
          "table": {
            "skipEmptyValues": false
          },
          "triggers": {
            "acknowledged": 2,
            "count": true,
            "minSeverity": 3
          }
        }
      ],
      "thresholds": [],
      "timeFrom": null,
      "timeRegions": [],
      "timeShift": null,
      "title": "Network interfaces",
      "tooltip": {
        "shared": true,
        "sort": 0,
        "value_type": "individual"
      },
      "type": "graph",
      "xaxis": {
        "buckets": null,
        "mode": "time",
        "name": null,
        "show": true,
        "values": []
      },
      "yaxes": [
        {
          "format": "Kbits",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": null,
          "show": true
        },
        {
          "format": "short",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": null,
          "show": true
        }
      ],
      "yaxis": {
        "align": false,
        "alignLevel": null
      }
    },
    {
      "columns": [],
      "datasource": "$datasource",
      "fontSize": "100%",
      "gridPos": {
        "h": 7,
        "w": 10,
        "x": 14,
        "y": 36
      },
      "id": 23,
      "links": [],
      "pageSize": 40,
      "scroll": true,
      "showHeader": true,
      "sort": {
        "col": 0,
        "desc": true
      },
      "styles": [
        {
          "alias": "Time",
          "dateFormat": "YYYY-MM-DD HH:mm:ss",
          "pattern": "Time",
          "type": "date"
        },
        {
          "alias": "Risultato Ping",
          "colorMode": "value",
          "colors": [
            "rgba(50, 172, 45, 0.97)",
            "#5195ce",
            "#c15c17"
          ],
          "dateFormat": "YYYY-MM-DD HH:mm:ss",
          "decimals": 2,
          "link": false,
          "mappingType": 1,
          "pattern": "Agent ping",
          "sanitize": false,
          "thresholds": [
            ""
          ],
          "type": "string",
          "unit": "none",
          "valueMaps": [
            {
              "text": "True",
              "value": "1"
            },
            {
              "text": "False",
              "value": ""
            }
          ]
        },
        {
          "alias": "",
          "colorMode": null,
          "colors": [
            "rgba(245, 54, 54, 0.9)",
            "rgba(237, 129, 40, 0.89)",
            "rgba(50, 172, 45, 0.97)"
          ],
          "decimals": 2,
          "pattern": "Time",
          "thresholds": [],
          "type": "number",
          "unit": "short"
        }
      ],
      "targets": [
        {
          "application": {
            "filter": "Zabbix agent"
          },
          "functions": [],
          "group": {
            "filter": "$gruppo"
          },
          "host": {
            "filter": "$VMdiscovered"
          },
          "item": {
            "filter": "Agent ping"
          },
          "mode": 0,
          "options": {
            "showDisabledItems": false,
            "skipEmptyValues": false
          },
          "refId": "A",
          "resultFormat": "time_series",
          "table": {
            "skipEmptyValues": false
          },
          "triggers": {
            "acknowledged": 2,
            "count": true,
            "minSeverity": 3
          }
        }
      ],
      "title": "Agent Ping",
      "transform": "timeseries_to_columns",
      "type": "table"
    }
  ],
  "refresh": "1m",
  "schemaVersion": 16,
  "style": "dark",
  "tags": [
      "Account",
      "ORGYYY",
      "ACCYYY",
      "DIVYYY"
  ],
  "templating": {
    "list": [
      {
        "current": {
          "text": "Zabbix Tenant PodTo1",
          "value": "Zabbix Tenant PodTo1"
        },
        "hide": 0,
        "label": "Zabbix Data Source",
        "name": "datasource",
        "options": [],
        "query": "alexanderzobnin-zabbix-datasource",
        "refresh": 1,
        "regex": "/.* Tenant.*/",
        "skipUrlSync": false,
        "type": "datasource"
      },
      {
        "allValue": null,
        "current": {
          "selected": true,
          "text": "XXXXX",
          "value": "XXXXX"
        },
        "hide": 2,
        "includeAll": false,
        "label": "Account",
        "multi": false,
        "name": "gruppo",
        "options": [
          {
            "selected": true,
            "text": "XXXXX",
            "value": "XXXXX"
          }
        ],
        "query": "XXXXX",
        "skipUrlSync": false,
        "type": "custom"
      },
      {
        "allValue": null,

        "datasource": "$datasource",
        "definition": "{$gruppo}{*}",
        "hide": 0,
        "includeAll": false,
        "label": "Server",
        "multi": false,
        "name": "VMdiscovered",
        "options": [],
        "query": "{$gruppo}{*}",
        "refresh": 1,
        "regex": "",
        "skipUrlSync": false,
        "sort": 0,
        "tagValuesQuery": "",
        "tags": [],
        "tagsQuery": "",
        "type": "query",
        "useTags": false
      }
    ]
  },
  "time": {
    "from": "now/d",
    "to": "now"
  },
  "timepicker": {
    "hidden": false,
    "refresh_intervals": [
      "1m",
      "5m",
      "10m",
      "30m",
      "1h"
    ],
    "time_options": [
      "5m",
      "15m",
      "1h",
      "6h",
      "12h",
      "24h",
      "2d",
      "7d",
      "30d"
    ]
  },
  "timezone": "",
  "title": "Resource-XXXXX",
  "version": 1
},
"folderid": 9999999999
}'''
{{/*
_helpers.tpl — Reusable template snippets

These are named templates called with {{ include "taskhub.xxx" . }}
throughout the other template files.
*/}}

{{/* Chart name */}}
{{- define "taskhub.name" -}}
{{- .Chart.Name }}
{{- end }}

{{/* Full release name — used as prefix for all resource names */}}
{{- define "taskhub.fullname" -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Common labels applied to every resource */}}
{{- define "taskhub.labels" -}}
app.kubernetes.io/name: {{ include "taskhub.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
{{- end }}

{{/* Selector labels — used in matchLabels (must be stable across upgrades) */}}
{{- define "taskhub.selectorLabels" -}}
app.kubernetes.io/name: {{ include "taskhub.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

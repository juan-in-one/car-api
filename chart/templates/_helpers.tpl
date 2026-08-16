{{/*
Nombre corto del chart (car-api).
*/}}
{{- define "car-api.name" -}}
{{- .Chart.Name -}}
{{- end -}}

{{/*
Nombre completo de los recursos: <release>-car-api. El nombre de "release" es el
que se le da al `helm install <release> ...`; permite instalar el mismo chart
varias veces en el clúster sin que los nombres choquen. Si el release ya se
llama igual que el chart (el caso normal aquí, ej. `helm install car-api chart/`),
no se duplica el nombre.
*/}}
{{- define "car-api.fullname" -}}
{{- if eq .Release.Name .Chart.Name -}}
{{- .Chart.Name -}}
{{- else -}}
{{- .Release.Name -}}-{{- .Chart.Name -}}
{{- end -}}
{{- end -}}

{{/*
Etiquetas comunes que se añaden a todos los recursos (buena práctica estándar
de Kubernetes/Helm para poder filtrar `kubectl get pods -l app.kubernetes.io/name=car-api`).
*/}}
{{- define "car-api.labels" -}}
app.kubernetes.io/name: {{ include "car-api.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/*
Subconjunto de etiquetas usado en el selector del Deployment/Service: deben ser
estables (no cambiar entre releases), por eso van aparte de "labels".
*/}}
{{- define "car-api.selectorLabels" -}}
app.kubernetes.io/name: {{ include "car-api.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

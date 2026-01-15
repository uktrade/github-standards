{{- range .}}
{{- range .Vulnerabilities}}
\n#### Severity:{{ .Severity | html }}\n{{ .VulnerabilityID | html }} {{ .Title | html }}\n{{ .Description | html }}\n
{{ end }}
{{- end }}
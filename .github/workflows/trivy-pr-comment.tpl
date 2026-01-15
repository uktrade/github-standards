{{- range .}}
Type: {{ .Type | html }}\n
Target: {{ .Target | html }}\n
{{- range .Vulnerabilities}}
\n#### Severity: {{ .Severity | html }}\n{{ .VulnerabilityID | html }} {{ .Title | html }}\n{{ .Description | html }}\n
{{ end }}
{{- range .Misconfigurations}}
\n#### Severity: {{ .Severity | html }}\n{{ .ID | html }} {{ .Title | html }}\n{{ .Description | html }}\n
{{ end }}
{{- end }}
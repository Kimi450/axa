{{ define "configuration" }}
    {{- if .Values.config }}
        {{- if .Values.config.values }}
            {{- if and .Values.config.values.annual_distance .Values.config.values.first_name .Values.config.values.last_name .Values.config.values.date_of_birth .Values.config.values.phone_number .Values.config.values.email .Values.config.values.occupation .Values.config.values.eir_code .Values.config.values.license_held .Values.config.values.prometheus_client_port .Values.config.values.registrations  }}
  linked-config.yaml: |-
{{- toYaml $.Values.config.values | toString | nindent 4 }}
            {{ else }} {{/* There is at least one missing argument, use config file instead */}}
{{ (.Files.Glob "linked-config.yaml").AsConfig | indent 2 }}
            {{- end }}
        {{- end }}
    {{- end }}
{{- end }}
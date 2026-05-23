```mermaid
classDiagram
  ABC <|-- BaseFilter
  BaseFilter <|-- CargoFilter
  BaseFilter <|-- CatFilter
  BaseFilter <|-- CurlFilter
  BaseFilter <|-- DockerFilter
  BaseFilter <|-- GitFilter
  BaseFilter <|-- GrepFilter
  BaseFilter <|-- KubectlFilter
  BaseFilter <|-- LintFilter
  BaseFilter <|-- LsFilter
  BaseFilter <|-- MakeFilter
  BaseFilter <|-- NpmFilter
  BaseFilter <|-- PackageManagerFilter
  BaseFilter <|-- PoetryFilter
  Group <|-- PytkGroup
  BaseFilter <|-- TerraformFilter
  BaseFilter <|-- TestFilter
  BaseFilter <|-- UvFilter
```

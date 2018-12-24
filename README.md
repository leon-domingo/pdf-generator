# Welcome to PDF generator

This a **[Flask](http://flask.pocoo.org/)** app which uses **[wkhtmltopdf](https://wkhtmltopdf.org/)** (to generate the PDF itself) and **[MongoDB](https://www.mongodb.com/)** (to implement a queue of processes), to create an **API-based service** that generate **PDFs from HTML**. Everything is “packaged” into a **[Docker](https://www.docker.com/)** [image](https://cloud.docker.com/u/leondomingo/repository/docker/leondomingo/pdf-generator), though you can deploy it as a set of services instead of a monolithic arquitecture.

You have to send the URL from which **wkhtmltopdf** will generate the PDF, among other parameters. So it's up to you to serve the HTML content that it'll be converted into a PDF

There's only one service in the API:

## /to-pdf
_Content-Type: application/json_
_Method: POST_

```json
{
  "url": "...",
  "headers": [["name", "value"], ...],
  "cookies": [["name", "value"], ...],
  "margins": [10, 10, 10, 10],
  "size: "A3",
  "viewport-size": "1200x1200",
  "attachments": ["...", ...]
}
```

### url

The URL to get the HTML page that will be converted to PDF.

### headers

Corresponds to the --custom-header parameter of wkhtmltopdf. You can indicate as many headers as you want. For example:

```json
{
  "headers": [
    ["Authorization", "mySecretToken"],
    ["X-MyCustom-Header", "my-custom-value"],
    ...
  ]
}
```

These headers will be included in the request to url, so it'll depend on your needs.

TIP: Use Authorization header to control access to “your” url, so it won't be accessible by anyone.

### cookies

Corresponds to the _--cookie_ parameter of **wkhtmltopdf**. You can add as many as you want and they all will be included in the request to **url**, so it depends on your needs. For example:

```json
{
  "cookies": [
    ["some-lang-cookie", "en"],
    ["foo", "bar-and-baz"],
    ...
  ]
}
```

### margins

Corresponds to the 4 parameters of **wkhtmltopdf** for _margin-top_, _margin-right_, _margin-bottom_ and _margin-left_.

### size
_defaut value:_ **A3**

Corresponds to the _-s_ / _--page-size_ parameter of **wkhtmltopdf**, which indicates the **paper size** of the resulting PDF. Possible values are A3, A4, Letter, ...
viewport-size

Corresponds to the _--viewport-size_ parameter of **wkhtmltopdf**, which indicates the **size of the window** the url will be viewed, in the form **WxH**. For example, **1200x1200**

### attachments

A list of **base64-encoded strings** representing the PDFs files to be added at the end of the resulting PDF. They'll be included in the same order as they come in the list.

**TIP**: If your generating a contract this can be used to include the **terms and conditions**.

### response

_Content-Type: application/json_
```json
{
  "status": <bool>,
  "pdf": "...",
}
```

### status

A boolean value depending on the result. **true** if it's been successful, or **false** if not.


### pdf

A **base64-enconded string** of the resulting **PDF** file, in case of success.

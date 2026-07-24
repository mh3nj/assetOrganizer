/*
illustrator_export.jsx

Illustrator automation:
- Export PNG preview
- Hide visible layers only
- Save document
*/


function exportPreview(path)
{
    var doc = app.activeDocument;
    var file = new File(path);
    var options = new ExportOptionsPNG24();
    options.transparency = true;
    doc.exportFile(file, ExportType.PNG24, options);
}


function hideVisibleLayers()
{
    var doc = app.activeDocument;
    for (var i = 0; i < doc.layers.length; i++)
    {
        processLayer(doc.layers[i]);
    }
}


function processLayer(layer)
{
    if (layer.visible)
    {
        layer.visible = false;
    }
    if (layer.layers && layer.layers.length)
    {
        for (var i = 0; i < layer.layers.length; i++)
        {
            processLayer(layer.layers[i]);
        }
    }
}


function saveDocument()
{
    app.activeDocument.save();
}

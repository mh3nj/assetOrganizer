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
    // Unlock first: a locked layer throws on `visible = false` and
    // aborts the loop, leaving random layers visible (and the file
    // big). Every step is isolated so one stubborn item never stops
    // the rest.
    try { layer.locked = false; } catch (e) {}
    if (layer.layers && layer.layers.length)
    {
        for (var i = 0; i < layer.layers.length; i++)
        {
            try { processLayer(layer.layers[i]); } catch (e) {}
        }
    }
    try
    {
        if (layer.pageItems && layer.pageItems.length)
        {
            for (var j = 0; j < layer.pageItems.length; j++)
            {
                try { layer.pageItems[j].locked = false; } catch (e) {}
            }
        }
    }
    catch (e) {}
    try
    {
        if (layer.visible)
        {
            layer.visible = false;
        }
    }
    catch (e) {}
}


function saveDocument()
{
    app.activeDocument.save();
}

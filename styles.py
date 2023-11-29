from hsd_constants import PALETTE

CSS = (
    '''
body {
    margin: 0;
    padding: 0;
}
.main-wrapper {
    padding: 1em 1em 3em 1em;
}
header {
    background: #555555;
    color: #ffffff;
    text-align: center;
    padding: 1em;
}
h1 {
    font-family: Helvetica, Arial, sans-serif;
}
#logo-main {
    width: 15em;
    margin: 0 auto;
}
.color-box {
    height: 100%;
    background:'''
    + str(PALETTE[1])
    + ''';
    color: #fff;
    padding: 2em;
    margin-top: 28px;
}
.accordion {
    background-color: #eee;
    cursor: pointer;
    padding: 18px;
    width: 100%;
    border: none;
    outline: none;
    text-align: center;
    font-size: 1.25em;
    color: #555555;
    font-weight: bold;
    transition: 0.9s;
}

.accordion:hover {
    background-color: #ccc;
}

.panel:first-of-type,
.panel.active-panel {
    max-height: none;
}
.panel,
.panel.active-panel:first-of-type {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.9s ease-out;
    border-bottom: 1px solid #ffffff;
}
@media (min-width: 1200px) {
    #logo-main {
        width: 15em;
        margin: 0;
    }

    .row {
        display: grid;
        grid-template-columns: repeat(12, 1fr);
        grid-template-rows: 1fr auto;
        column-gap: 0.75em;
    }

    .grid-fourth {
        grid-column: auto / span 3;
    }

    .grid-third {
        grid-column: auto / span 4;
    }

    .grid-two-thirds {
        grid-column: auto / span 8;
    }

    .grid-half {
        grid-column: auto / span 6;
    }

    .grid-three-fourths {
        grid-column: auto / span 9;
    }

    .grid-full {
        grid-column: auto / span 12;
    }

    .grid-large-third {
        grid-column: auto / span 5;
    }

    .grid-small-slice {
        grid-column: auto / span 2;
    }

}
'''
)

declare module 'react-plotly.js' {
  import type { Component } from 'react'
  import type { Data, Layout, Config, PlotMouseEvent, ClickAnnotationEvent, PlotHoverEvent, PlotSelectionEvent, PlotRelayoutEvent, PlotRestyleEvent, FrameAnimationEvent, ButtonClickedEvent, LegendClickEvent, SliderChangeEvent, SliderEndEvent, SliderStartEvent, Frame } from 'plotly.js'

  interface Figure {
    data: Data[]
    layout: Partial<Layout>
    frames?: Frame[]
  }

  interface PlotlyChartProps {
    data: Data[]
    layout?: Partial<Layout>
    config?: Partial<Config>
    frames?: Frame[]
    style?: React.CSSProperties
    className?: string
    useResizeHandler?: boolean
    debug?: boolean
    onInitialized?: (figure: Readonly<Figure>, graphDiv: HTMLElement) => void
    onUpdate?: (figure: Readonly<Figure>, graphDiv: HTMLElement) => void
    onPurge?: (figure: Readonly<Figure>, graphDiv: HTMLElement) => void
    onError?: (error: Error) => void
    divId?: string
    onClick?: (event: Readonly<PlotMouseEvent>) => void
    onClickAnnotation?: (event: Readonly<ClickAnnotationEvent>) => void
    onDoubleClick?: () => void
    onHover?: (event: Readonly<PlotHoverEvent>) => void
    onUnhover?: (event: Readonly<PlotMouseEvent>) => void
    onSelected?: (event: Readonly<PlotSelectionEvent>) => void
    onDeselect?: () => void
    onRelayout?: (event: Readonly<PlotRelayoutEvent>) => void
    onRestyle?: (event: Readonly<PlotRestyleEvent>) => void
    onRedraw?: () => void
    onAnimated?: () => void
    onAnimatingFrame?: (event: Readonly<FrameAnimationEvent>) => void
    onAfterExport?: () => void
    onAfterPlot?: () => void
    onAutoSize?: () => void
    onBeforeExport?: () => void
    onButtonClicked?: (event: Readonly<ButtonClickedEvent>) => void
    onLegendClick?: (event: Readonly<LegendClickEvent>) => boolean
    onLegendDoubleClick?: (event: Readonly<LegendClickEvent>) => boolean
    onSliderChange?: (event: Readonly<SliderChangeEvent>) => void
    onSliderEnd?: (event: Readonly<SliderEndEvent>) => void
    onSliderStart?: (event: Readonly<SliderStartEvent>) => void
    onTransitioning?: () => void
    onTransitionInterrupted?: () => void
    revision?: number
  }

  export default class Plot extends Component<PlotlyChartProps> {}
}

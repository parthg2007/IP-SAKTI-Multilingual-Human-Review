import assert from 'node:assert/strict'
import { setImmediate } from 'node:timers/promises'
import { test } from 'node:test'
import { createScrollSequence } from '../src/components/scrollSequence.js'

const manifest = { width: 16, height: 12, frames: 240, framesPerStrip: 10, stripCount: 24 }

function environment(t, fetchResponse) {
  const bitmaps = []
  const draws = []
  const originalDecoder = globalThis.createImageBitmap
  globalThis.createImageBitmap = async (strip) => {
    const bitmap = { strip, closed: false, close() { this.closed = true } }
    bitmaps.push(bitmap)
    return bitmap
  }
  t.after(() => {
    if (originalDecoder) globalThis.createImageBitmap = originalDecoder
    else delete globalThis.createImageBitmap
  })
  const response = (url) => ({ ok: true, blob: async () => Number(url.match(/strip-(\d+)/)[1]) })
  t.mock.method(globalThis, 'fetch', fetchResponse || (async (url) => response(url)))
  const canvas = {
    dataset: {},
    getContext: () => ({ drawImage: (...args) => draws.push(args), clearRect() {} }),
  }
  const sequence = createScrollSequence(canvas, manifest, '/animation/')
  t.after(() => sequence.dispose())
  return { bitmaps, draws, canvas, sequence, response }
}

test('renders the correct frame after forward jumps and reverse scrolling, with bounded decoded memory', async (t) => {
  const { sequence, draws, canvas, bitmaps } = environment(t)
  for (const frame of [0, 117, 3, 239, -10]) {
    sequence.render(frame)
    await setImmediate()
    const expected = Math.max(0, Math.min(239, frame))
    const [bitmap, , sourceY] = draws.at(-1)
    assert.equal(bitmap.strip, Math.floor(expected / 10))
    assert.equal(sourceY, (expected % 10) * manifest.height)
    assert.ok(bitmaps.filter((item) => !item.closed).length <= 3)
  }
  assert.equal(canvas.dataset.ready, 'true')
  sequence.dispose()
  assert.ok(bitmaps.every((bitmap) => bitmap.closed))
  assert.equal(canvas.dataset.ready, undefined)
})

test('discards late decoded images after navigation or a reduced-motion change', async (t) => {
  const requests = []
  const { sequence, draws, bitmaps, canvas, response } = environment(t, (url, options) => new Promise((resolve) => {
    requests.push({ url, options, resolve })
  }))
  sequence.render(0)
  assert.equal(requests.length, 2)
  sequence.dispose()
  assert.ok(requests.every(({ options }) => options.signal.aborted))
  requests.forEach(({ resolve, url }) => resolve(response(url)))
  await setImmediate()
  assert.equal(draws.length, 0)
  assert.ok(bitmaps.every((bitmap) => bitmap.closed))
  assert.equal(canvas.dataset.ready, undefined)
})

test('keeps the poster when a strip fails and continues when a later stage loads', async (t) => {
  const { sequence, draws, canvas } = environment(t, async (url) => ({
    ok: !url.endsWith('strip-00.webp'),
    blob: async () => Number(url.match(/strip-(\d+)/)[1]),
  }))
  sequence.render(0)
  await setImmediate()
  assert.equal(draws.length, 0)
  assert.equal(canvas.dataset.ready, undefined)
  sequence.render(15)
  await setImmediate()
  assert.equal(draws.at(-1)[0].strip, 1)
  assert.equal(canvas.dataset.ready, 'true')
})
